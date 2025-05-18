# ishares-etf-data Examples

This directory contains example scripts demonstrating how to use the `ishares-etf-data` library for various tasks related to Russell 1000 holdings data.

> **IMPORTANT**: This is an **UNOFFICIAL** package not affiliated with BlackRock or iShares. See the full disclaimer in the main [README.md](../README.md) file before using this package. By using these examples, you accept all responsibility and liability.

## How the Library Works

The `ishares-etf-data` library provides access to iShares Russell 1000 ETF holdings through:

1. **API Integration**:
   - The library connects to iShares JSON API endpoints to retrieve holdings data
   - Primary endpoints include:
     - Date availability endpoint: Returns available dates with published holdings
     - Holdings endpoint: Returns detailed holding data for a specific date
   - Web scraping is used for extracting the latest available date from the dropdown on the product page

2. **Data Processing**:
   - Raw JSON data is parsed into a structured `HoldingData` class
   - Holdings are mapped to a consistent format with ticker, name, sector, weight, etc.
   - The library removes asterisks (*) from ticker symbols automatically
   - Methods provide filtering, sorting, and analysis capabilities

3. **Smart Date Handling**:
   - The library includes a fallback mechanism to always get the latest data
   - HTML parsing is used when newer dates are available on the website but not in the API
   - The `get_latest_holdings()` function ensures you always get the most recent data

The library is designed to be robust, handling network issues, unexpected data formats, and API changes gracefully.

## Available Examples

1. **save_tickers_by_date.py**: Extracts tickers for all available dates and saves them to separate text files.
2. **analyze_sector_changes.py**: Analyzes sector weights over time and tracks changes between dates.
3. **save_and_load_holdings.py**: Demonstrates how to save and load holdings data to/from JSON files, and shows the flexible date format options.
4. **get_latest_holdings.py**: Fetches the most recent available holdings data and saves the equity tickers to a file.
5. **verify_latest_date.py**: Demonstrates the improved date handling to ensure you always get the most recent available date.

## Running the Examples

### Prerequisites

Make sure you have installed the library first:

```bash
# From the root directory of the repository
pip install -e .
```

### Running the Ticker Extraction Example

This example fetches all available dates for Russell 1000 holdings, extracts the tickers for each date, and saves them to separate text files in the `output` directory.

```bash
# From the examples directory
python save_tickers_by_date.py
```

The files will be saved as `YYYYMMDD_ishares_russell_1000_etf.txt` in the `output` directory, with one ticker per line.

If you want to limit the number of dates processed (to avoid making too many API requests), you can modify the `MAX_DATES` constant in the script.

### Running the Latest Date Verification Example

This example demonstrates the improved date handling to ensure you always get the most recent available date:

```bash
# From the examples directory
python verify_latest_date.py
```

The script will:
1. Fetch the latest date from the HTML dropdown
2. Fetch available dates from the API endpoint
3. Compare the results to show which is more recent
4. Attempt to get holdings for both dates to verify data availability

This is especially useful when the latest date's data isn't showing up in the regular API calls but is available through the website.

### Running the Latest Holdings Example

This example fetches the most recent available holdings data using the improved date handling:

```bash
# From the examples directory
python get_latest_holdings.py
```

The script will use the `get_latest_holdings()` function which internally uses the improved date handling to ensure you get the most recent data. It extracts equity tickers and saves them to a file.

### Running the Sector Analysis Example

This example analyzes sector weights over time and tracks changes between dates.

```bash
# From the examples directory
python analyze_sector_changes.py
```

This will generate two files in the `output` directory:
- `russell_sector_weights.csv`: A CSV file showing sector weights over the 5 most recent dates.
- `sector_changes.txt`: A text file showing the changes in sector weights between the two most recent dates.

### Running the Serialization Example

This example demonstrates how to save and load holdings data to/from JSON files, and showcases the flexible date format options.

```bash
# From the examples directory
python save_and_load_holdings.py
```

This will:
1. Fetch the most recent holdings data
2. Save it to a JSON file in the `output` directory
3. Load it back from the file
4. Demonstrate using different date formats for input (YYYYMMDD strings, YYYY-MM-DD strings, date objects)
5. Demonstrate different return formats for dates (strings, date objects, datetime objects)

## Flexible Date Handling

The library now supports flexible date handling:

1. **Input Date Formats**: All functions that accept dates can handle:
   - YYYYMMDD format strings (e.g., "20250318")
   - Common date format strings (e.g., "2025-03-18", "03/18/2025")
   - datetime.date objects
   - datetime.datetime objects

2. **Output Date Formats**: The `get_available_holding_dates()` function can return dates in different formats:
   - Strings (default): `get_available_holding_dates(return_format="string")`
   - Date objects: `get_available_holding_dates(return_format="date")`
   - Datetime objects: `get_available_holding_dates(return_format="datetime")`

3. **Getting the Latest Data**: The library now includes improved date handling to ensure you always get the most recent available data:
   - `get_latest_date_from_html()`: Extracts the latest date from the dropdown on the iShares website
   - `get_latest_holdings()`: Fetches holdings for the most recent available date

## Customizing the Examples

Feel free to modify these examples to suit your needs. Here are some ideas:

- Change the `MAX_DATES` or `NUM_DATES` constants to analyze more or fewer dates.
- Modify the file naming templates.
- Add additional analysis or visualization (e.g., plotting sector weights over time).
- Implement filtering by specific sectors or tickers.
- Use different date formats based on your preference.

## API Rate Limiting

Be mindful of the number of requests you're making to the iShares API. The examples include small delays between requests to avoid overwhelming the API. If you're processing many dates, consider increasing these delays or implementing more sophisticated rate limiting.

## Acknowledgments

This project was assisted and co-written by Vibe Coding. 