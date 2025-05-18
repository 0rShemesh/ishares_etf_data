"""iShares ETF Data Library: Fetch holdings for iShares Russell 1000 ETF.

DISCLAIMER: This is an UNOFFICIAL tool not affiliated with BlackRock or iShares.
The author(s) assume no liability for any damages resulting from its use.
See full disclaimer in the package README.

This package is for educational and informational purposes only.
"""

from .core import (
    get_available_holding_dates,
    get_holdings,
    get_latest_holdings,
    get_latest_date_from_html,
    HoldingData,
    clear_cache,
    # Error types
    ApiError,
    NetworkError,
    DataFormatError,
    InvalidDateError,
)

__all__ = [
    'get_available_holding_dates',
    'get_holdings',
    'get_latest_holdings',
    'get_latest_date_from_html',
    'HoldingData',
    'clear_cache',
    'ApiError',
    'NetworkError',
    'DataFormatError',
    'InvalidDateError',
]

__version__ = "0.1.0" # Keep in sync with pyproject.toml and setup.py 