#!/usr/bin/env python3
"""
Example script that demonstrates the improved date handling in ishares_etf_data.

This script:
1. Gets the latest date from the HTML dropdown
2. Gets available dates from the API
3. Compares the results to verify we're getting the most recent date
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
    get_latest_date_from_html,
    get_available_holding_dates,
    get_holdings,
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

logger = logging.getLogger("date_verification")


def main():
    """Main function demonstrating date handling."""
    logger.info("Demonstrating improved date handling")
    
    try:
        # Get the latest date from the HTML dropdown
        logger.info("1. Fetching latest date from HTML dropdown...")
        html_date = get_latest_date_from_html()
        logger.info(f"   Result: {html_date} ({datetime.strptime(html_date, '%Y%m%d').date()})")
        
        # Get available dates from the regular API
        logger.info("\n2. Fetching available dates from API...")
        api_dates = get_available_holding_dates()
        if api_dates:
            top_5_dates = api_dates[:5]
            date_display = []
            for d in top_5_dates:
                date_obj = datetime.strptime(d, '%Y%m%d').date()
                date_display.append(f"{d} ({date_obj})")
            logger.info(f"   Top 5 API dates: {', '.join(date_display)}")
        else:
            logger.warning("   No dates returned from API")
            
        # Compare the results
        logger.info("\n3. Comparing results:")
        if not api_dates:
            logger.info("   Cannot compare - no API dates available")
        else:
            api_latest = api_dates[0]
            html_date_obj = datetime.strptime(html_date, '%Y%m%d').date()
            api_date_obj = datetime.strptime(api_latest, '%Y%m%d').date()
            
            logger.info(f"   HTML date: {html_date} ({html_date_obj})")
            logger.info(f"   API date: {api_latest} ({api_date_obj})")
            
            if html_date_obj > api_date_obj:
                logger.info(f"   ✓ HTML date is more recent by {(html_date_obj - api_date_obj).days} days")
            elif html_date_obj < api_date_obj:
                logger.info(f"   ⚠ API date is more recent by {(api_date_obj - html_date_obj).days} days")
            else:
                logger.info(f"   ✓ Both dates match")
                
        # Attempt to get holdings for both dates to verify availability
        logger.info("\n4. Verifying data availability:")
        
        # Try HTML date
        logger.info(f"   Checking holdings for HTML date ({html_date})...")
        try:
            html_holdings = get_holdings(html_date)
            logger.info(f"   ✓ Successfully retrieved {len(html_holdings)} holdings")
            logger.info(f"     First 3 tickers: {', '.join(html_holdings.tickers[:3])}")
        except Exception as e:
            logger.error(f"   ✗ Failed to get holdings for HTML date: {e}")
            
        # Try API date if different
        if api_dates and api_dates[0] != html_date:
            logger.info(f"\n   Checking holdings for API date ({api_dates[0]})...")
            try:
                api_holdings = get_holdings(api_dates[0])
                logger.info(f"   ✓ Successfully retrieved {len(api_holdings)} holdings")
                logger.info(f"     First 3 tickers: {', '.join(api_holdings.tickers[:3])}")
            except Exception as e:
                logger.error(f"   ✗ Failed to get holdings for API date: {e}")
        
        logger.info("\nDate verification complete")
        
    except (NetworkError, DataFormatError) as e:
        logger.error(f"Error during verification: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 