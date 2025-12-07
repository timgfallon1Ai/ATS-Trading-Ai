# ats/backtester2/data_loader.py

from __future__ import annotations

from typing import Dict, List

import pandas as pd


class DataLoader:
    """Unified loader for multi-symbol historical data.
    Assumes CSV or Parquet with standard O/H/L/C/V columns.
    """

    def load(self, symbols: List[str], start: str, end: str) -> Dict[str, pd.DataFrame]:
        data = {}

        for sym in symbols:
            path_csv = f"data/{sym}.csv"
            path_parq = f"data/{sym}.parquet"

            try:
                df = pd.read_parquet(path_parq)
            except Exception:
                df = pd.read_csv(path_csv)

            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.set_index("timestamp")

            df = df.loc[start:end]

            data[sym] = df

        return data
