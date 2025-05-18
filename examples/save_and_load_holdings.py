#!/usr/bin/env python3
"""
Example script that demonstrates how to use the ishares_etf_data library's
serialization and deserialization functionality.

This script:
1. Fetches the most recent available date's holdings
2. Saves the holdings data to a JSON file
3. Loads the holdings data back from the JSON file
4. Performs some analyses on the loaded data to verify it works correctly
"""

import os
import sys
import logging
from pathlib import Path
import time
import json
import datetime

# Add the parent directory to sys.path to import the library when running from examples/
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.ishares_etf_data import (
    get_available_holding_dates,
    get_holdings,
    HoldingData,
    NetworkError,
    DataFormatError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Log to console
    ]
)

logger = logging.getLogger("holdings_serialization")

# Constants
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
HOLDINGS_JSON_FILE = "latest_holdings.json"

def ensure_output_dir():
    """Create the output directory if it doesn't exist."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    logger.info(f"Output directory: {OUTPUT_DIR}")

def fetch_and_save_holdings():
    """Fetch the most recent holdings and save to a JSON file."""
    try:
        logger.info("Fetching available dates...")
        dates = get_available_holding_dates()
        
        if not dates:
            logger.error("No dates found!")
            return None
        
        # Get the most recent date
        latest_date = dates[0]
        logger.info(f"Fetching holdings for the most recent date: {latest_date}")
        
        # Get the holdings data using the string format
        holdings = get_holdings(latest_date)
        
        # Save to JSON file
        output_path = OUTPUT_DIR / HOLDINGS_JSON_FILE
        holdings.to_json(str(output_path))
        
        logger.info(f"Saved holdings data to {output_path}")
        return holdings
        
    except (NetworkError, DataFormatError) as e:
        logger.error(f"Failed to fetch and save holdings data: {e}")
        return None

def load_holdings():
    """Load holdings data from the previously saved JSON file."""
    try:
        input_path = OUTPUT_DIR / HOLDINGS_JSON_FILE
        if not input_path.exists():
            logger.error(f"File not found: {input_path}")
            return None
            
        logger.info(f"Loading holdings data from {input_path}")
        holdings = HoldingData.from_json(file_path=str(input_path))
        
        logger.info(f"Successfully loaded holdings for date {holdings.date}")
        return holdings
        
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load holdings data: {e}")
        return None

def analyze_holdings(holdings):
    """Perform some basic analyses on the holdings data to verify it works."""
    if not holdings:
        logger.error("No holdings data to analyze")
        return
    
    logger.info(f"Analyzing holdings for date: {holdings.date}")
    logger.info(f"Total number of holdings: {len(holdings)}")
    
    # Check tickers
    tickers = holdings.tickers
    logger.info(f"Number of tickers: {len(tickers)}")
    if tickers:
        logger.info(f"First 5 tickers: {tickers[:5]}")
    
    # Check sectors
    sectors = holdings.sectors
    logger.info(f"Number of sectors: {len(sectors)}")
    if sectors:
        logger.info(f"Sectors: {', '.join(list(sectors)[:5])}")
        
        # Example of sector analysis
        for sector in list(sectors)[:3]:
            sector_holdings = holdings.filter_by_sector(sector)
            logger.info(f"Number of holdings in {sector}: {len(sector_holdings)}")

    # Check asset classes
    asset_classes = holdings.asset_classes
    logger.info(f"Number of asset classes: {len(asset_classes)}")
    if asset_classes:
        logger.info(f"Asset classes: {', '.join(list(asset_classes))}")
        
        # Example of asset class filtering
        for asset_class in list(asset_classes)[:2]:
            asset_class_holdings = holdings.filter_by_asset_class(asset_class)
            logger.info(f"Number of holdings in asset class {asset_class}: {len(asset_class_holdings)}")
    
    # Sector weights
    sector_weights = holdings.get_sector_weights()
    top_sectors = sorted(sector_weights.items(), key=lambda x: x[1], reverse=True)[:3]
    logger.info("Top 3 sectors by weight:")
    for sector, weight in top_sectors:
        logger.info(f"  {sector}: {weight:.2f}%")

def demonstrate_date_formats():
    """Demonstrate fetching holdings with different date formats."""
    try:
        logger.info("\nDemonstrating different date format support:")
        
        # Get available dates first
        dates = get_available_holding_dates()
        if not dates or len(dates) < 2:
            logger.error("Not enough dates available for demonstration")
            return
        
        date_to_use = dates[1]  # Use the second most recent date
        
        # 1. Using a date string in YYYYMMDD format (original format)
        logger.info(f"1. Using YYYYMMDD string: {date_to_use}")
        holdings1 = get_holdings(date_to_use)
        logger.info(f"   Fetched {len(holdings1)} holdings for {holdings1.date}")
        
        # 2. Using a date string in YYYY-MM-DD format
        date_hyphen = f"{date_to_use[:4]}-{date_to_use[4:6]}-{date_to_use[6:]}"
        logger.info(f"2. Using YYYY-MM-DD string: {date_hyphen}")
        holdings2 = get_holdings(date_hyphen)
        logger.info(f"   Fetched {len(holdings2)} holdings for {holdings2.date}")
        
        # 3. Using a date object
        date_obj = datetime.datetime.strptime(date_to_use, "%Y%m%d").date()
        logger.info(f"3. Using datetime.date object: {date_obj}")
        holdings3 = get_holdings(date_obj)
        logger.info(f"   Fetched {len(holdings3)} holdings for {holdings3.date}")
        
        logger.info("All date formats processed successfully!")
        
    except Exception as e:
        logger.error(f"Error during date format demonstration: {e}")

def demonstrate_return_formats():
    """Demonstrate getting available dates in different return formats."""
    try:
        logger.info("\nDemonstrating different return formats for available dates:")
        
        # 1. Get dates as strings (default)
        string_dates = get_available_holding_dates(return_format="string")
        logger.info(f"1. Dates as strings (first 3): {string_dates[:3]}")
        logger.info(f"   Type of first element: {type(string_dates[0]).__name__}")
        
        # 2. Get dates as date objects
        date_objects = get_available_holding_dates(return_format="date")
        logger.info(f"2. Dates as date objects (first 3): {date_objects[:3]}")
        logger.info(f"   Type of first element: {type(date_objects[0]).__name__}")
        
        # 3. Get dates as datetime objects
        datetime_objects = get_available_holding_dates(return_format="datetime")
        logger.info(f"3. Dates as datetime objects (first 3): {datetime_objects[:3]}")
        logger.info(f"   Type of first element: {type(datetime_objects[0]).__name__}")
        
        logger.info("All return formats processed successfully!")
        
    except Exception as e:
        logger.error(f"Error during return format demonstration: {e}")

def main():
    """Main function."""
    logger.info("Starting holdings serialization example")
    
    # Make sure output directory exists
    ensure_output_dir()
    
    # Step 1: Fetch and save holdings
    logger.info("Step 1: Fetching and saving holdings data")
    original_holdings = fetch_and_save_holdings()
    
    if original_holdings:
        # Wait a moment to simulate time passing
        time.sleep(1)
        
        # Step 2: Load holdings from file
        logger.info("\nStep 2: Loading holdings data from file")
        loaded_holdings = load_holdings()
        
        if loaded_holdings:
            # Step 3: Analyze loaded holdings
            logger.info("\nStep 3: Analyzing loaded holdings data")
            analyze_holdings(loaded_holdings)
            
            # Step 4: Demonstrate different date formats for input
            demonstrate_date_formats()
            
            # Step 5: Demonstrate different return formats for dates
            demonstrate_return_formats()
    
    logger.info("Finished holdings serialization example")

if __name__ == "__main__":
    main() 