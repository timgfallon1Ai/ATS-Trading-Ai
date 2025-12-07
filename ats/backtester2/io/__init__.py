"""Unified I/O module for Backtester2.

This package provides:
- UBF loaders (parquet & memory)
- Schema definitions
- Normalization utilities
- Validation utilities
"""

from .normalization import normalize_bars
from .schema import Bar, UBFSchema
from .ubf_loader import UBFLoader
from .validation import validate_bars

__all__ = [
    "UBFSchema",
    "Bar",
    "UBFLoader",
    "normalize_bars",
    "validate_bars",
]
