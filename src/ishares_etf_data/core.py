import requests
import datetime
import functools
import logging
import json
import re
from typing import List, Dict, Any, Optional, Set, Callable, TypeVar, cast, Union

# Set up logging
logger = logging.getLogger(__name__)

# Type variable for caching decorator
T = TypeVar('T')

# URLs for iShares data
AVAILABLE_DATES_URL = "https://www.ishares.com/us/products/239707/ishares-russell-1000-etf/1467271812595.ajax?tab=distributions&fileType=json&subtab=table"
HOLDINGS_URL_TEMPLATE = "https://www.ishares.com/us/products/239707/ishares-russell-1000-etf/1467271812596.ajax?fileType=json&tab=all&asOfDate={date_str}"
HOLDINGS_HTML_URL = "https://www.ishares.com/us/products/239707/ishares-russell-1000-etf"

# Default timeout for requests in seconds
DEFAULT_TIMEOUT = 10

class ApiError(Exception):
    """Base exception for all API-related errors."""
    pass

class NetworkError(ApiError):
    """Exception raised for network connectivity issues."""
    pass

class DataFormatError(ApiError):
    """Exception raised when API data doesn't match expected format."""
    pass

class InvalidDateError(ValueError):
    """Exception raised when the provided date format is invalid."""
    pass

def cache_result(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator that caches the result of a function call.
    """
    cache = {}
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Create a cache key from the function arguments
        key = str(args) + str(sorted(kwargs.items()))
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]
    
    # Add a clear_cache method to the wrapper function
    def clear_cache():
        cache.clear()
    
    wrapper.clear_cache = clear_cache  # type: ignore
    return wrapper

def format_date(date_obj: Union[str, datetime.date, datetime.datetime]) -> str:
    """
    Convert various date formats to 'YYYYMMDD' string format required by the API.
    
    Args:
        date_obj: A date as string in various formats, or a date/datetime object.
                 Supported string formats include 'YYYYMMDD', 'YYYY-MM-DD', etc.
    
    Returns:
        A date string in 'YYYYMMDD' format.
        
    Raises:
        InvalidDateError: If the date format cannot be parsed.
    """
    try:
        # If it's already a date or datetime object
        if isinstance(date_obj, (datetime.date, datetime.datetime)):
            return date_obj.strftime("%Y%m%d")
        
        # If it's already in the correct format (YYYYMMDD)
        if isinstance(date_obj, str):
            if len(date_obj) == 8 and date_obj.isdigit():
                # Validate it's a real date by parsing it
                datetime.datetime.strptime(date_obj, "%Y%m%d")
                return date_obj
                
            # Try common formats
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y"]:
                try:
                    parsed_date = datetime.datetime.strptime(date_obj, fmt)
                    return parsed_date.strftime("%Y%m%d")
                except ValueError:
                    continue
            
            # If we get here, none of the formats matched
            raise ValueError(f"Could not parse date string: {date_obj}")
        
        raise ValueError(f"Unsupported date type: {type(date_obj)}")
        
    except ValueError as e:
        raise InvalidDateError(f"Invalid date format: {e}") from e

def _parse_raw_value(item_value: Any) -> Any:
    """Extracts the 'raw' value if item_value is a dictionary, otherwise returns the value itself."""
    if isinstance(item_value, dict) and 'raw' in item_value:
        return item_value['raw']
    return item_value

def _map_raw_item(unmapped_item: List[Any]) -> Dict[str, Any]:
    """
    Maps a raw holding item from the iShares API to a structured dictionary.
    This version uses a predefined mapping for clarity and maintainability.
    """
    if not isinstance(unmapped_item, list) or len(unmapped_item) < 17:
        # Handle cases where the item is not as expected to prevent IndexError
        logger.warning(f"Unmapped item has unexpected format or length: {unmapped_item}")
        return {key: None for key in [
            'ticker', 'name', 'sector', 'asset_class', 'market_value', 'weight',
            'notional_value', 'shares', 'cusip', 'isin', 'sedol', 'price',
            'location', 'exchange', 'currency', 'fx_rate', 'maturity'
        ]}

    # Defines the structure: "new_key_name": (index_in_unmapped_item, parsing_function)
    # Using _parse_raw_value for fields that might have a {'display': ..., 'raw': ...} structure.
    # For fields that are direct values, no specific parsing function is needed beyond direct access.
    mapping_rules = {
        'ticker': (0, None),
        'name': (1, None),
        'sector': (2, None),
        'asset_class': (3, None),
        'market_value': (4, _parse_raw_value),
        'weight': (5, _parse_raw_value),
        'notional_value': (6, _parse_raw_value),
        'shares': (7, _parse_raw_value),
        'cusip': (8, None),
        'isin': (9, None),
        'sedol': (10, None),
        'price': (11, _parse_raw_value),
        'location': (12, None),
        'exchange': (13, None),
        'currency': (14, None),
        'fx_rate': (15, None),  # Assuming fx_rate is usually a direct string or number
        'maturity': (16, None)
    }

    mapped_dict = {}
    for key, (index, parser_func) in mapping_rules.items():
        try:
            value = unmapped_item[index]
            if parser_func:
                mapped_dict[key] = parser_func(value)
            else:
                # Clean ticker symbols by removing asterisks
                if key == 'ticker' and value and isinstance(value, str):
                    value = value.replace('*', '')
                mapped_dict[key] = value
        except IndexError:
            logger.debug(f"Index {index} for key '{key}' is out of bounds for item: {unmapped_item}")
            mapped_dict[key] = None
    return mapped_dict


class HoldingData:
    """
    Represents the holding data for iShares Russell 1000 ETF for a specific date.
    """
    def __init__(self, date_str: str, raw_data: List[List[Any]]):
        self._date_str = date_str
        # Stores the original list of lists from the JSON (e.g., content of 'aaData')
        self._raw_items_list = raw_data 
        self._mapped_data: Optional[List[Dict[str, Any]]] = None
        self._ticker_to_holding: Optional[Dict[str, Dict[str, Any]]] = None
        self._sectors: Optional[Set[str]] = None
        self._asset_classes: Optional[Set[str]] = None

    @property
    def date(self) -> datetime.date:
        """The date of the holdings data."""
        return datetime.datetime.strptime(self._date_str, "%Y%m%d").date()

    @property
    def raw_json_items(self) -> List[List[Any]]:
        """The raw list of holding items (e.g., aaData) as returned from the API."""
        return self._raw_items_list

    @property
    def holdings(self) -> List[Dict[str, Any]]:
        """List of all holdings, with each holding mapped to a structured dictionary."""
        if self._mapped_data is None:
            self._mapped_data = [_map_raw_item(item) for item in self._raw_items_list]
        return self._mapped_data

    @property
    def tickers(self) -> List[str]:
        """
        List of all tickers/symbols in the holdings.
        Asterisks (*) are removed from ticker symbols.
        """
        # Ensure 'ticker' exists and is not None before including
        # Asterisks are already removed in _map_raw_item, but this is a double check
        return [item['ticker'] for item in self.holdings if item.get('ticker') is not None]
    
    @property
    def sectors(self) -> Set[str]:
        """Set of unique sectors represented in the holdings."""
        if self._sectors is None:
            self._sectors = {
                item['sector'] for item in self.holdings 
                if item.get('sector') is not None and item['sector'] != '-'
            }
        return self._sectors
    
    @property
    def asset_classes(self) -> Set[str]:
        """Set of unique asset classes represented in the holdings."""
        if self._asset_classes is None:
            self._asset_classes = {
                item['asset_class'] for item in self.holdings 
                if item.get('asset_class') is not None and item['asset_class'] != '-'
            }
        return self._asset_classes

    def get_holding_by_ticker(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the detailed data for a specific ticker.
        
        Any asterisks (*) in the input ticker are removed for the lookup.

        Args:
            ticker: The ticker symbol to search for.

        Returns:
            A dictionary containing the holding data for the ticker, or None if not found.
        """
        # Clean any asterisks from the input ticker
        clean_ticker = ticker.replace('*', '') if ticker else ticker
        
        # Build a ticker -> holding map for faster lookups if needed multiple times
        if self._ticker_to_holding is None:
            self._ticker_to_holding = {}
            for item in self.holdings:
                item_ticker = item.get('ticker')
                if item_ticker:
                    # Asterisks are already removed in _map_raw_item, but this is a double check
                    self._ticker_to_holding[item_ticker] = item
        
        return self._ticker_to_holding.get(clean_ticker)

    def filter_by_sector(self, sector: str) -> List[Dict[str, Any]]:
        """
        Filters holdings by sector.

        Args:
            sector: The sector to filter by.

        Returns:
            A list of holdings that belong to the specified sector.
        """
        return [item for item in self.holdings if item.get('sector') == sector]
        
    def filter_by_asset_class(self, asset_class: str) -> List[Dict[str, Any]]:
        """
        Filters holdings by asset class.

        Args:
            asset_class: The asset class to filter by.

        Returns:
            A list of holdings that belong to the specified asset class.
        """
        return [item for item in self.holdings if item.get('asset_class') == asset_class]

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the HoldingData object to a dictionary suitable for JSON serialization.

        Returns:
            A dictionary representation of the HoldingData.
        """
        return {
            'date_str': self._date_str,
            'raw_data': self._raw_items_list
        }
    
    def to_json(self, file_path: Optional[str] = None) -> Optional[str]:
        """
        Serialize the HoldingData object to JSON.

        Args:
            file_path: Optional path to save the JSON to a file.
                      If None, returns the JSON string.

        Returns:
            JSON string if file_path is None, otherwise None.
        """
        data_dict = self.to_dict()
        
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(data_dict, f, indent=2)
            logger.info(f"Saved holdings data to {file_path}")
            return None
        else:
            return json.dumps(data_dict, indent=2)
    
    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> 'HoldingData':
        """
        Create a HoldingData object from a dictionary.

        Args:
            data_dict: Dictionary containing HoldingData attributes.

        Returns:
            A new HoldingData instance.
        """
        required_keys = ['date_str', 'raw_data']
        for key in required_keys:
            if key not in data_dict:
                raise ValueError(f"Missing required key: {key}")
        
        return cls(date_str=data_dict['date_str'], raw_data=data_dict['raw_data'])
    
    @classmethod
    def from_json(cls, json_str: Optional[str] = None, file_path: Optional[str] = None) -> 'HoldingData':
        """
        Create a HoldingData object from JSON.

        Args:
            json_str: JSON string representation of HoldingData.
            file_path: Path to a file containing JSON data.
                      Either json_str or file_path must be provided.

        Returns:
            A new HoldingData instance.

        Raises:
            ValueError: If neither json_str nor file_path is provided,
                      or if the JSON data is missing required fields.
        """
        if json_str is None and file_path is None:
            raise ValueError("Either json_str or file_path must be provided")
        
        if file_path:
            logger.info(f"Loading holdings data from {file_path}")
            with open(file_path, 'r') as f:
                data_dict = json.load(f)
        else:
            data_dict = json.loads(json_str)
        
        return cls.from_dict(data_dict)

    def get_total_market_value(self) -> float:
        """
        Calculates the total market value of all holdings.

        Returns:
            The sum of market values, or 0 if market values are not available.
        """
        total = 0.0
        for item in self.holdings:
            market_value = item.get('market_value')
            if market_value is not None:
                try:
                    total += float(market_value)
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert market_value to float: {market_value}")
        return total

    def get_sector_weights(self) -> Dict[str, float]:
        """
        Calculates the weight of each sector as a percentage of the total.

        Returns:
            A dictionary mapping sectors to their weight percentage.
        """
        sector_totals: Dict[str, float] = {}
        total_weight = 0.0
        
        # Sum weights by sector
        for item in self.holdings:
            sector = item.get('sector')
            weight = item.get('weight')
            
            if sector and weight is not None:
                try:
                    weight_float = float(weight)
                    sector_totals[sector] = sector_totals.get(sector, 0.0) + weight_float
                    total_weight += weight_float
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert weight to float: {weight}")
        
        # Normalize by total if needed
        if total_weight > 0:
            return {sector: (weight / total_weight * 100) for sector, weight in sector_totals.items()}
        return sector_totals

    def __len__(self) -> int:
        """Returns the number of holdings."""
        return len(self.holdings)

    def __repr__(self) -> str:
        return f"<HoldingData date='{self._date_str}', items={len(self._raw_items_list)}>"


@cache_result
def get_available_holding_dates(
    timeout: int = DEFAULT_TIMEOUT,
    return_format: str = "string"
) -> Union[List[str], List[datetime.date], List[datetime.datetime]]:
    """
    Fetches the available dates for which iShares Russell 1000 ETF holdings data exists.

    Args:
        timeout: Request timeout in seconds.
        return_format: Format to return dates in. Options:
                      "string" - returns dates as strings in 'YYYYMMDD' format (default)
                      "date" - returns dates as datetime.date objects
                      "datetime" - returns dates as datetime.datetime objects

    Returns:
        A list of dates in the specified format, sorted most recent first.
    
    Raises:
        NetworkError: If the network request fails.
        DataFormatError: If the response JSON is not in the expected format.
        ValueError: If an invalid return_format is specified.
    """
    if return_format not in ["string", "date", "datetime"]:
        raise ValueError(f"Invalid return_format: {return_format}. Must be 'string', 'date', or 'datetime'")
    
    try:
        response = requests.get(AVAILABLE_DATES_URL, timeout=timeout)
        response.raise_for_status() 
        data = json.loads(response.content)
        
        date_strings = set()  # Use a set for automatic duplicate handling
        if "table" in data and "aaData" in data["table"]:
            for item_list in data["table"]["aaData"]:
                # Ensure item_list is not empty and its first element is a dict with 'raw' key
                if item_list and isinstance(item_list[0], dict) and "raw" in item_list[0]:
                    date_value = str(item_list[0]["raw"])
                    # Basic validation for date format (YYYYMMDD)
                    if len(date_value) == 8 and date_value.isdigit():
                        date_strings.add(date_value)
        else:
            raise DataFormatError("Unexpected JSON structure for available dates in API response.")
        
        # Sort dates in descending order
        sorted_date_strings = sorted(list(date_strings), reverse=True)
        
        if return_format == "string":
            return sorted_date_strings
        
        # Convert to date/datetime objects if requested
        if return_format == "date":
            return [datetime.datetime.strptime(date_str, "%Y%m%d").date() 
                    for date_str in sorted_date_strings]
        
        # Must be "datetime" at this point
        return [datetime.datetime.strptime(date_str, "%Y%m%d") 
                for date_str in sorted_date_strings]

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while fetching available dates: {e}")
        raise NetworkError(f"Failed to fetch available dates: {e}") from e
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error parsing available dates JSON: {e}")
        raise DataFormatError(f"Error parsing available dates JSON: {e}") from e


def get_holdings(date_obj: Union[str, datetime.date, datetime.datetime], timeout: int = DEFAULT_TIMEOUT) -> HoldingData:
    """
    Fetches the iShares Russell 1000 ETF holdings for a specific date.

    Args:
        date_obj: The date for which to fetch holdings. Can be:
                 - A string in 'YYYYMMDD' or other common formats like 'YYYY-MM-DD'
                 - A datetime.date or datetime.datetime object
        timeout: Request timeout in seconds.

    Returns:
        A HoldingData object containing the parsed holdings.

    Raises:
        InvalidDateError: If the date format is invalid.
        NetworkError: If the network request fails.
        DataFormatError: If the response JSON is not in the expected format.
    """
    try:
        # Convert the date to the required format
        date_str = format_date(date_obj)
        
        url = HOLDINGS_URL_TEMPLATE.format(date_str=date_str)
        logger.info(f"Fetching holdings for date {date_str}")
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        
        raw_data_response = json.loads(response.content)

        # The API might return the list directly, or nested under 'aaData'
        if isinstance(raw_data_response, dict) and "aaData" in raw_data_response:
            actual_holdings_list = raw_data_response["aaData"]
        elif isinstance(raw_data_response, list):
            actual_holdings_list = raw_data_response
        else:
            raise DataFormatError("Holdings data from API is not in the expected list or {'aaData': list} format.")
        
        if not actual_holdings_list:
            logger.warning(f"No holdings found for date {date_str}")
            return HoldingData(date_str=date_str, raw_data=[])
            
        if not all(isinstance(item, list) for item in actual_holdings_list):
            raise DataFormatError("Individual holding items in the API response are not in the expected list format.")

        return HoldingData(date_str=date_str, raw_data=actual_holdings_list)

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while fetching holdings for date {date_str}: {e}")
        raise NetworkError(f"Failed to fetch holdings for date {date_str}: {e}") from e
    except (ValueError, KeyError, TypeError) as e:
        if isinstance(e, InvalidDateError):
            raise
        logger.error(f"Error parsing holdings JSON for date {date_str}: {e}")
        raise DataFormatError(f"Error parsing holdings JSON for date {date_str}: {e}") from e

def clear_cache() -> None:
    """
    Clears any cached data, forcing fresh data to be fetched on the next call.
    """
    # Access the clear_cache method we attached to the wrapper function
    cast(Callable[[], None], get_available_holding_dates.clear_cache)()

def get_latest_date_from_html(timeout: int = DEFAULT_TIMEOUT) -> str:
    """
    Extracts the most recent available date from the iShares Russell 1000 ETF holdings page.
    
    This is useful when the latest date's data isn't available through the regular API endpoint,
    but is listed in the dropdown on the main page.
    
    Args:
        timeout: Request timeout in seconds
        
    Returns:
        The latest available date in 'YYYYMMDD' format
        
    Raises:
        NetworkError: If there's an issue with the network request
        DataFormatError: If the HTML cannot be parsed correctly
    """
    try:
        logger.info("Fetching HTML to extract latest available date")
        response = requests.get(HOLDINGS_HTML_URL, timeout=timeout)
        response.raise_for_status()
        html_content = response.text
        
        # Look for the date dropdown and extract all option values
        # The pattern matches: <option value="YYYYMMDD">
        date_pattern = r'<option value="(\d{8})"'
        
        # Find all matches (all dates in the dropdown)
        date_matches = re.findall(date_pattern, html_content)
        
        if not date_matches:
            raise DataFormatError("Could not find date options in the HTML content")
        
        # Validate all dates and convert to datetime objects for accurate sorting
        valid_dates = []
        for date_str in date_matches:
            if len(date_str) == 8 and date_str.isdigit():
                try:
                    # Parse to validate and create date object for sorting
                    date_obj = datetime.datetime.strptime(date_str, "%Y%m%d")
                    valid_dates.append((date_str, date_obj))
                except ValueError:
                    logger.warning(f"Skipping invalid date format: {date_str}")
        
        if not valid_dates:
            raise DataFormatError("No valid dates found in HTML content")
        
        # Sort by date (descending) to get the most recent date first
        sorted_dates = sorted(valid_dates, key=lambda x: x[1], reverse=True)
        latest_date = sorted_dates[0][0]
        
        logger.info(f"Latest available date from HTML: {latest_date}")
        return latest_date
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while fetching HTML content: {e}")
        raise NetworkError(f"Failed to fetch HTML content: {e}") from e
    except Exception as e:
        logger.error(f"Error extracting date from HTML: {e}")
        raise DataFormatError(f"Error extracting date from HTML: {e}") from e

def get_latest_holdings(timeout: int = DEFAULT_TIMEOUT) -> HoldingData:
    """
    Fetches the most recent available holdings for the iShares Russell 1000 ETF.
    
    This function:
    1. Gets the latest available date by parsing the HTML dropdown
    2. Uses that date to fetch the latest holdings data
    
    Args:
        timeout: Request timeout in seconds
        
    Returns:
        A HoldingData object containing the latest available holdings
        
    Raises:
        NetworkError: If there's an issue with the network request
        DataFormatError: If the data cannot be parsed correctly
    """
    try:
        # Get the latest available date
        latest_date = get_latest_date_from_html(timeout=timeout)
        
        # Use that date to fetch the holdings
        logger.info(f"Fetching latest holdings for date {latest_date}")
        holdings = get_holdings(latest_date, timeout=timeout)
        
        # Check if we got any holdings
        if len(holdings) == 0:
            logger.warning(f"No holdings data available for latest date {latest_date}")
            
            # Try getting available dates and use the most recent one that has data
            available_dates = get_available_holding_dates(timeout=timeout)
            if available_dates:
                fallback_date = available_dates[0]
                logger.info(f"Falling back to most recent date with confirmed data: {fallback_date}")
                holdings = get_holdings(fallback_date, timeout=timeout)
                
        return holdings
        
    except (NetworkError, DataFormatError) as e:
        logger.error(f"Error getting latest holdings: {e}")
        raise

# Example Usage
if __name__ == '__main__':
    # Configure logging for testing
    logging.basicConfig(level=logging.INFO, 
                         format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("Attempting to use the iShares ETF data library functions...")
    
    print("Fetching available holding dates...")
    try:
        available_dates = get_available_holding_dates()
        if available_dates:
            print(f"Found {len(available_dates)} available dates. Most recent 5: {available_dates[:5]}")
            
            latest_date = available_dates[0]
            print(f"\nFetching holdings for the latest available date: {latest_date}...")
            holdings_data = get_holdings(latest_date)
            
            print(f"Successfully fetched holdings for date: {holdings_data.date}")
            print(f"Total number of holdings: {len(holdings_data)}")
            
            if holdings_data.tickers:
                print(f"First 5 tickers: {holdings_data.tickers[:5]}")
                
                # Display sector information
                print(f"\nSectors found: {len(holdings_data.sectors)}")
                print(f"Sector examples: {list(holdings_data.sectors)[:3]}")
                
                # Get information about a specific ticker
                example_ticker = holdings_data.tickers[0]
                details = holdings_data.get_holding_by_ticker(example_ticker)
                if details:
                    print(f"\nDetails for ticker {example_ticker}:")
                    print(f"  Name: {details.get('name', 'N/A')}")
                    print(f"  Sector: {details.get('sector', 'N/A')}")
                    print(f"  Weight (%): {details.get('weight', 'N/A')}")
                
                # Example of sector weights
                print("\nSector weights (%):")
                sector_weights = holdings_data.get_sector_weights()
                for sector, weight in sorted(sector_weights.items(), key=lambda x: x[1], reverse=True)[:5]:
                    print(f"  {sector}: {weight:.2f}%")
                
                # Filter by a sector
                first_sector = next(iter(holdings_data.sectors)) if holdings_data.sectors else None
                if first_sector:
                    sector_holdings = holdings_data.filter_by_sector(first_sector)
                    print(f"\nNumber of holdings in sector '{first_sector}': {len(sector_holdings)}")
                    
            else:
                print("No tickers found in the holdings data.")

        else:
            print("No available holding dates were found.")

        # Test with a specific past date from the example
        print("\nTesting with a specific past date (e.g., 20230927)...")
        try:
            past_date_str = "20230927"
            past_holdings = get_holdings(past_date_str)
            print(f"Successfully fetched holdings for {past_holdings.date}")
            print(f"Number of holdings: {len(past_holdings)}")
            if past_holdings.tickers:
                print(f"First 5 tickers: {past_holdings.tickers[:5]}")
        except Exception as e_past:
            print(f"Could not fetch holdings for {past_date_str}: {e_past}")

    except Exception as e:
        print(f"An error occurred during the example usage: {e}") 