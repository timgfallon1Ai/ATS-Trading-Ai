# ats/backtester2/data_window.py

from __future__ import annotations

from typing import Any

import pandas as pd


class DataWindow:
    """Provides timestamp-indexed slices of the historical data."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.sort_index()
        self.timestamps = list(self.df.index)

    def get(self, ts) -> Any:
        # Return the full row (OHLCV)
        return self.df.loc[ts]
