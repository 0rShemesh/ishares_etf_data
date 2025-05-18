#!/usr/bin/env python3
"""
Example script that demonstrates how to use the get_latest_holdings function
to fetch the most recent available holdings for the iShares Russell 1000 ETF.

This script:
1. Fetches the latest available holdings 
2. Displays summary information about those holdings
3. Saves the equity tickers to a text file
"""

import sys
import logging
from datetime import datetime
from pathlib import Path

# Add the parent directory to sys.path to import the library when running from examples/
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.ishares_etf_data import (
    get_latest_holdings,
    get_latest_date_from_html,
    get_available_holding_dates,
    NetworkError,
    DataFormatError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger("latest_holdings")

# Constants
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
FILE_NAME_TEMPLATE = "{date}_ishares_russell_1000_etf_latest.txt"
EQUITY_ONLY = True  # Set to True to save only equity tickers


def ensure_output_dir():
    """Create the output directory if it doesn't exist."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    logger.info(f"Output directory: {OUTPUT_DIR}")


def save_tickers_to_file(date_str, tickers):
    """Save a list of tickers to a text file, one ticker per line."""
    # Skip saving if there are no tickers
    if not tickers:
        logger.info(f"No tickers found, skipping file creation")
        return
    
    file_path = OUTPUT_DIR / FILE_NAME_TEMPLATE.format(date=date_str)
    
    with open(file_path, "w") as f:
        for ticker in tickers:
            f.write(f"{ticker}\n")
    
    logger.info(f"Saved {len(tickers)} tickers to {file_path}")


def verify_latest_date():
    """
    Verify that we're getting the most recent date by comparing methods.
    """
    try:
        # Get date from HTML parsing (most reliable for the latest date)
        html_date = get_latest_date_from_html()
        logger.info(f"Latest date from HTML dropdown: {html_date}")
        
        # Get the dates from the regular API endpoint for comparison
        api_dates = get_available_holding_dates()
        logger.info(f"Top 3 dates from API: {', '.join(api_dates[:3]) if api_dates else 'None'}")
        
        # Parse both for better comparison display
        html_date_obj = datetime.strptime(html_date, "%Y%m%d").date()
        
        if api_dates:
            api_date_obj = datetime.strptime(api_dates[0], "%Y%m%d").date()
            
            if html_date_obj > api_date_obj:
                logger.info(f"HTML date ({html_date_obj}) is more recent than API date ({api_date_obj})")
            elif html_date_obj < api_date_obj:
                logger.info(f"API date ({api_date_obj}) is more recent than HTML date ({html_date_obj})")
            else:
                logger.info(f"HTML and API dates match: {html_date_obj}")
        
        return html_date
        
    except Exception as e:
        logger.error(f"Error verifying latest date: {e}")
        return None


def main():
    """Main function."""
    logger.info("Fetching latest Russell 1000 ETF holdings")
    
    # Make sure output directory exists
    ensure_output_dir()
    
    # First verify the latest date to show improved handling
    latest_date = verify_latest_date()
    
    try:
        # Get the latest holdings
        logger.info("Fetching the latest holdings data...")
        holdings = get_latest_holdings()
        
        # Compare with the date we got earlier
        if latest_date:
            holdings_date_str = holdings.date.strftime("%Y%m%d")
            if holdings_date_str == latest_date:
                logger.info(f"✓ Successfully retrieved holdings for the latest date: {holdings.date}")
            else:
                logger.warning(f"⚠ Holdings date ({holdings_date_str}) doesn't match expected latest ({latest_date})")
        
        # Display info about the holdings
        logger.info(f"Total number of holdings: {len(holdings)}")
        
        # Get tickers
        if EQUITY_ONLY:
            # Get equity-only holdings
            asset_classes = holdings.asset_classes
            logger.info(f"Found {len(asset_classes)} asset classes: {', '.join(asset_classes)}")
            
            equity_holdings = holdings.filter_by_asset_class("Equity")
            equity_tickers = [item.get('ticker') for item in equity_holdings if item.get('ticker')]
            
            logger.info(f"Found {len(equity_tickers)} equity tickers out of {len(holdings.tickers)} total")
            tickers = equity_tickers
        else:
            # Get all tickers
            tickers = holdings.tickers
            logger.info(f"Found {len(tickers)} tickers")
        
        # Display the first few tickers
        if tickers:
            logger.info(f"First 5 tickers: {', '.join(tickers[:5])}")
            
        # Save tickers to file
        date_str = holdings.date.strftime("%Y%m%d")
        save_tickers_to_file(date_str, tickers)
        
        logger.info("Successfully processed latest holdings")
        
    except (NetworkError, DataFormatError) as e:
        logger.error(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 