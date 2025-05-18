#!/usr/bin/env python3
"""
This script extracts equity-only tickers from iShares Russell 1000 ETF holdings.

It performs the following steps:
1. Fetches all available dates for Russell 1000 holdings
2. For each date, fetches the holdings data
3. Filters holdings by asset class "Equity"
4. Extracts the equity-only tickers
5. Saves each date's equity tickers to a separate text file in the 'output' directory
"""

import os
import sys
import logging
import time
from datetime import datetime
from pathlib import Path

# Add the parent directory to sys.path to import the library when running from examples/
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.ishares_etf_data import (
    get_available_holding_dates,
    get_holdings,
    NetworkError,
    DataFormatError,
    InvalidDateError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Log to console
    ]
)

logger = logging.getLogger("russell_equity")

# Constants
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
FILE_NAME_TEMPLATE = "{date}_ishares_russell_1000_etf_equities.txt"
MAX_DATES = None  # Set to a number to limit the number of dates processed, or None for all
ASSET_CLASS = "Equity"  # We'll filter for this asset class


def ensure_output_dir():
    """Create the output directory if it doesn't exist."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    logger.info(f"Output directory: {OUTPUT_DIR}")


def save_tickers_to_file(date_str, tickers):
    """Save a list of tickers to a text file, one ticker per line."""
    # Skip saving if there are no tickers
    if not tickers:
        logger.info(f"No equity tickers found for date {date_str}, skipping file creation")
        return
    
    file_path = OUTPUT_DIR / FILE_NAME_TEMPLATE.format(date=date_str)
    
    with open(file_path, "w") as f:
        for ticker in tickers:
            f.write(f"{ticker}\n")
    
    logger.info(f"Saved {len(tickers)} equity tickers to {file_path}")


def get_equity_tickers(holdings):
    """Extract tickers from equity holdings only."""
    # Get equity-only holdings
    equity_holdings = holdings.filter_by_asset_class(ASSET_CLASS)
    
    # Extract tickers from equity holdings
    return [item.get('ticker') for item in equity_holdings if item.get('ticker') is not None]


def process_all_dates():
    """
    Fetch holdings data for all available dates and save equity tickers to text files.
    """
    try:
        logger.info("Fetching available dates...")
        # Get dates as date objects for better display
        dates = get_available_holding_dates(return_format="date")
        
        if not dates:
            logger.warning("No dates found!")
            return
        
        logger.info(f"Found {len(dates)} available dates")
        
        # Apply limit if set
        if MAX_DATES is not None:
            dates = dates[:MAX_DATES]
            logger.info(f"Processing first {MAX_DATES} dates")
        
        # Process each date
        for i, date_obj in enumerate(dates):
            try:
                logger.info(f"Processing date {i+1}/{len(dates)}: {date_obj}")
                
                # Use date object directly
                logger.info(f"Fetching holdings for {date_obj}...")
                
                # Get the holdings data using the date object
                holdings = get_holdings(date_obj)
                
                # Get asset classes for reporting
                asset_classes = holdings.asset_classes
                logger.info(f"Found {len(asset_classes)} asset classes: {', '.join(asset_classes)}")
                
                # Get equity-only tickers
                equity_tickers = get_equity_tickers(holdings)
                
                # Calculate percentage of equity holdings
                all_tickers = holdings.tickers
                equity_percentage = (len(equity_tickers) / len(all_tickers) * 100) if all_tickers else 0
                
                logger.info(f"Found {len(equity_tickers)} equity tickers out of {len(all_tickers)} total "
                           f"({equity_percentage:.1f}%)")
                
                # Convert to string format for filename (YYYYMMDD)
                date_str = date_obj.strftime("%Y%m%d")
                
                # Save tickers to file (only if there are any)
                save_tickers_to_file(date_str, equity_tickers)
                
                # Add a small delay to avoid overwhelming the API
                if i < len(dates) - 1:
                    time.sleep(1)
                    
            except NetworkError as e:
                logger.error(f"Network error for date {date_obj}: {e}")
                continue
            except (DataFormatError, InvalidDateError) as e:
                logger.error(f"Data error for date {date_obj}: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error for date {date_obj}: {e}")
                continue
        
        logger.info("All dates processed successfully")
        
    except Exception as e:
        logger.error(f"Failed to process dates: {e}")


def main():
    """Main function."""
    logger.info("Starting Russell 1000 equity ticker extraction")
    
    # Make sure output directory exists
    ensure_output_dir()
    
    # Process all dates
    process_all_dates()
    
    logger.info("Finished processing")


if __name__ == "__main__":
    main() 