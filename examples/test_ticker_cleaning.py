#!/usr/bin/env python3
"""
This script tests the feature that removes asterisks from ticker symbols.

It downloads the most recent holdings data and:
1. Checks if any tickers originally had asterisks
2. Verifies they were properly removed
3. Tests lookup by ticker with and without asterisks
"""

import sys
import logging
from pathlib import Path

# Add the parent directory to sys.path to import the library when running from examples/
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.ishares_etf_data import get_available_holding_dates, get_holdings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger("ticker_test")

def check_original_tickers_for_asterisks(holdings_data):
    """Check if any tickers in the raw data contain asterisks."""
    asterisk_tickers = []
    
    for raw_item in holdings_data.raw_json_items:
        if not raw_item or len(raw_item) == 0:
            continue
            
        # The ticker is the first item in each raw item
        raw_ticker = raw_item[0]
        if isinstance(raw_ticker, str) and '*' in raw_ticker:
            asterisk_tickers.append(raw_ticker)
    
    return asterisk_tickers

def test_ticker_handling():
    """Test how the library handles tickers with asterisks."""
    logger.info("Testing asterisk removal from ticker symbols")
    
    # Get several dates to check
    dates = get_available_holding_dates()
    if not dates:
        logger.error("No dates available")
        return
    
    # Check 5 recent dates and 5 from further back (if available)
    # This increases our chances of finding tickers with asterisks
    dates_to_check = []
    
    # Recent dates
    recent_count = min(5, len(dates))
    dates_to_check.extend(dates[:recent_count])
    
    # Older dates (if available)
    older_indices = [25, 50, 75, 90, 99]  # Try to get dates further back
    for idx in older_indices:
        if idx < len(dates):
            dates_to_check.append(dates[idx])
    
    logger.info(f"Will check {len(dates_to_check)} dates in total")
    
    for i, date in enumerate(dates_to_check):
        logger.info(f"Checking date {i+1}/{len(dates_to_check)}: {date}")
        
        # Get holdings data
        holdings = get_holdings(date)
        
        # Check if any original tickers had asterisks
        asterisk_tickers = check_original_tickers_for_asterisks(holdings)
        
        if asterisk_tickers:
            logger.info(f"Found {len(asterisk_tickers)} tickers with asterisks in the raw data for date {date}:")
            for ticker in asterisk_tickers[:10]:  # Show first 10 at most
                logger.info(f"  {ticker}")
            
            # Check that asterisks were removed in the processed tickers
            logger.info("Verifying that asterisks were removed in the processed tickers:")
            
            for ticker_with_asterisk in asterisk_tickers[:5]:  # Test first 5 at most
                # Get cleaned version
                clean_ticker = ticker_with_asterisk.replace('*', '')
                
                # Check if it's in the tickers list
                if clean_ticker in holdings.tickers:
                    logger.info(f"  ✓ {ticker_with_asterisk} -> {clean_ticker} (properly cleaned)")
                    
                    # Test lookup by ticker with asterisk
                    holding_via_asterisk = holdings.get_holding_by_ticker(ticker_with_asterisk)
                    if holding_via_asterisk:
                        logger.info(f"  ✓ Lookup by ticker WITH asterisk works: {ticker_with_asterisk}")
                    else:
                        logger.error(f"  ✗ Lookup by ticker WITH asterisk fails: {ticker_with_asterisk}")
                        
                    # Test lookup by ticker without asterisk 
                    holding_via_clean = holdings.get_holding_by_ticker(clean_ticker)
                    if holding_via_clean:
                        logger.info(f"  ✓ Lookup by ticker WITHOUT asterisk works: {clean_ticker}")
                    else:
                        logger.error(f"  ✗ Lookup by ticker WITHOUT asterisk fails: {clean_ticker}")
                else:
                    logger.error(f"  ✗ {clean_ticker} not found in processed tickers")
                    
            # We found some, no need to check more dates
            return
    
    # If we get here, we didn't find any tickers with asterisks
    logger.info("No tickers with asterisks found in any of the checked dates")
    
    # Perform a test with a manually added asterisk
    holdings = get_holdings(dates[0])  # Use most recent date
    if holdings.tickers:
        test_ticker = holdings.tickers[0]
        logger.info(f"Testing with manually modified ticker: {test_ticker} -> {test_ticker}*")
        
        # Try lookup with artificially added asterisk
        test_ticker_with_asterisk = test_ticker + '*'
        result = holdings.get_holding_by_ticker(test_ticker_with_asterisk)
        
        if result:
            logger.info(f"  ✓ Lookup by ticker WITH artificial asterisk works")
        else:
            logger.error(f"  ✗ Lookup by ticker WITH artificial asterisk fails")

if __name__ == "__main__":
    test_ticker_handling() 