# ats/backtester2/loader.py

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterator, List

import pandas as pd
import pyarrow.parquet as pq

from .interfaces import (
    BarFeed,
    BarIterator,
    UBFBar,
)


# ===============================
# TIME-ALIGNED ITERATOR
# ===============================
class _TimeAlignedBarIterator:
    def __init__(self, frames: Dict[str, pd.DataFrame], symbols: List[str]):
        self.frames = frames
        self.symbols = symbols

        # Create a unified sorted timeline from ALL symbols
        all_ts = set()
        for df in frames.values():
            all_ts.update(df.index)

        self.timeline = sorted(all_ts)

    def __iter__(self) -> Iterator[Dict[str, UBFBar]]:
        for ts in self.timeline:
            out: Dict[str, UBFBar] = {}

            for sym in self.symbols:
                df = self.frames[sym]
                if ts in df.index:
                    row = df.loc[ts]
                    out[sym] = {
                        "symbol": sym,
                        "timestamp": int(ts),
                        "open": float(row.open),
                        "high": float(row.high),
                        "low": float(row.low),
                        "close": float(row.close),
                        "volume": float(row.volume),
                        "vwap": float(row.vwap) if "vwap" in row else float(row.close),
                    }

            if out:
                yield out


# ===============================
# UNIFIED BAR FEED
# ===============================
class UnifiedBarFeed(BarFeed):
    def __init__(self, parquet_folder: str, symbols: List[str]):
        self.parquet_folder = Path(parquet_folder)
        self.symbols = symbols

        self.frames: Dict[str, pd.DataFrame] = {}

        for sym in symbols:
            file = self.parquet_folder / f"{sym}.parquet"
            if not file.exists():
                raise FileNotFoundError(f"UBF file missing: {file}")

            table = pq.read_table(file)
            df = table.to_pandas()

            if "timestamp" not in df.columns:
                raise ValueError(f"UBF missing timestamp column: {file}")

            df = df.sort_values("timestamp")
            df = df.set_index("timestamp")

            self.frames[sym] = df

    def get_iterator(self) -> BarIterator:
        return _TimeAlignedBarIterator(self.frames, self.symbols)
