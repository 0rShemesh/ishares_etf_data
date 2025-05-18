#!/usr/bin/env python3
"""
Example script that demonstrates how to analyze sector weights over time.

This script:
1. Fetches holdings for the most recent dates
2. Analyzes how sector weights change over time
3. Saves a report to a CSV file in the 'output' directory
"""

import os
import sys
import logging
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Union, Set

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

logger = logging.getLogger("russell_sectors")

# Constants
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_FILE = "russell_sector_weights.csv"
NUM_DATES = 5  # Number of most recent dates to analyze


def ensure_output_dir():
    """Create the output directory if it doesn't exist."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    logger.info(f"Output directory: {OUTPUT_DIR}")


def analyze_sectors():
    """
    Analyze sector weights for the most recent dates and save a report.
    """
    try:
        logger.info("Fetching available dates...")
        # Get dates as datetime objects for easier manipulation
        date_objects = get_available_holding_dates(return_format="date")
        
        if not date_objects:
            logger.warning("No dates found!")
            return
        
        # Take only the most recent N dates
        date_objects = date_objects[:NUM_DATES]
        logger.info(f"Analyzing sector weights for the {len(date_objects)} most recent dates")
        
        # Store sector weights by date - use date object as key
        all_sector_weights: Dict[datetime.date, Dict[str, float]] = {}
        all_sectors: Set[str] = set()
        
        # Process each date
        for date_obj in date_objects:
            try:
                logger.info(f"Fetching holdings for {date_obj}...")
                
                # Get the holdings data, directly passing the date object
                holdings = get_holdings(date_obj)
                
                # Get sector weights
                sector_weights = holdings.get_sector_weights()
                logger.info(f"Found {len(sector_weights)} sectors for {date_obj}")
                
                # Store the weights and update the set of all sectors
                all_sector_weights[date_obj] = sector_weights
                all_sectors.update(sector_weights.keys())
                
            except Exception as e:
                logger.error(f"Error processing date {date_obj}: {e}")
        
        # Write results to CSV
        if all_sector_weights:
            write_sector_report(date_objects, all_sectors, all_sector_weights)
        else:
            logger.warning("No sector data found")
        
    except Exception as e:
        logger.error(f"Failed to analyze sectors: {e}")


def write_sector_report(
    date_objects: List[datetime.date],
    all_sectors: Set[str],
    all_sector_weights: Dict[datetime.date, Dict[str, float]]
):
    """Write sector weights to a CSV file."""
    output_path = OUTPUT_DIR / OUTPUT_FILE
    
    with open(output_path, 'w', newline='') as csvfile:
        # Create CSV writer
        writer = csv.writer(csvfile)
        
        # Write header row with dates formatted as YYYY-MM-DD
        header = ["Sector"] + [date_obj.strftime("%Y-%m-%d") for date_obj in date_objects]
        writer.writerow(header)
        
        # Sort sectors alphabetically
        sorted_sectors = sorted(all_sectors)
        
        # Write each sector's weights across dates
        for sector in sorted_sectors:
            row = [sector]
            for date_obj in date_objects:
                # Get weight for this sector and date, or 0 if not present
                weight = all_sector_weights.get(date_obj, {}).get(sector, 0)
                row.append(f"{weight:.2f}%")
            writer.writerow(row)
    
    logger.info(f"Saved sector weights report to {output_path}")


def analyze_sector_changes():
    """Analyze and report on the most significant sector weight changes."""
    try:
        logger.info("Fetching available dates...")
        # Get dates as date objects
        date_objects = get_available_holding_dates(return_format="date")
        
        if len(date_objects) < 2:
            logger.warning("Need at least two dates to compare sector changes")
            return
        
        # Get the two most recent dates for comparison
        latest_date = date_objects[0]
        previous_date = date_objects[1]
        
        logger.info(f"Comparing sectors between {latest_date} and {previous_date}")
        
        # Get holdings for both dates using date objects
        latest_holdings = get_holdings(latest_date)
        previous_holdings = get_holdings(previous_date)
        
        # Get sector weights
        latest_weights = latest_holdings.get_sector_weights()
        previous_weights = previous_holdings.get_sector_weights()
        
        # Calculate changes
        changes: List[Tuple[str, float]] = []
        for sector in set(latest_weights.keys()) | set(previous_weights.keys()):
            latest = latest_weights.get(sector, 0)
            previous = previous_weights.get(sector, 0)
            change = latest - previous
            changes.append((sector, change))
        
        # Sort by absolute change
        changes.sort(key=lambda x: abs(x[1]), reverse=True)
        
        # Output the results
        logger.info(f"Sector weight changes ({latest_date} vs {previous_date}):")
        
        output_path = OUTPUT_DIR / "sector_changes.txt"
        with open(output_path, 'w') as f:
            f.write(f"Sector weight changes between {latest_date} and {previous_date}:\n\n")
            
            for sector, change in changes:
                direction = "+" if change > 0 else ""
                line = f"{sector}: {direction}{change:.2f}%"
                f.write(line + "\n")
                logger.info(line)
        
        logger.info(f"Saved sector changes report to {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to analyze sector changes: {e}")


def main():
    """Main function."""
    logger.info("Starting Russell 1000 sector analysis")
    
    # Make sure output directory exists
    ensure_output_dir()
    
    # Analyze sector weights over time
    analyze_sectors()
    
    # Analyze sector weight changes between the two most recent dates
    analyze_sector_changes()
    
    logger.info("Finished sector analysis")


if __name__ == "__main__":
    main() 