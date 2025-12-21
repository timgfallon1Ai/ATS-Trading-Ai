from pathlib import Path
from typing import List, Optional

import pandas as pd

from .types import Bar


def load_bars_from_csv(path: str, symbol: Optional[str] = None) -> List[Bar]:
    """
    Load OHLCV bars from a CSV file.

    Required columns (case-insensitive):
      - timestamp OR datetime OR date
      - open, high, low, close
    Optional:
      - volume (defaults to 0)
      - symbol (if missing, you must pass symbol=...)

    Returns: list[Bar] sorted by timestamp ascending.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"CSV not found: {p}")

    df = pd.read_csv(p)
    if df.empty:
        raise ValueError(f"CSV contains no rows: {p}")

    df.columns = [str(c).strip().lower() for c in df.columns]

    ts_col = None
    for c in ("timestamp", "datetime", "date", "time"):
        if c in df.columns:
            ts_col = c
            break
    if ts_col is None:
        raise ValueError("CSV must include one of: timestamp, datetime, date, time")

    required = ["open", "high", "low", "close"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")

    if "volume" not in df.columns:
        df["volume"] = 0.0

    if "symbol" in df.columns:
        if symbol is not None:
            df["symbol"] = symbol
    else:
        if symbol is None:
            raise ValueError("CSV has no 'symbol' column; pass --symbol")
        df["symbol"] = symbol

    df[ts_col] = pd.to_datetime(df[ts_col], utc=True, errors="coerce")
    df = df.dropna(subset=[ts_col]).copy()
    df = df.sort_values(ts_col)

    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["open", "high", "low", "close"]).copy()

    bars: List[Bar] = []
    for row in df.to_dict(orient="records"):
        ts = pd.Timestamp(row[ts_col]).to_pydatetime().isoformat()
        bars.append(
            Bar(
                timestamp=ts,
                symbol=str(row["symbol"]),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row.get("volume", 0.0) or 0.0),
            )
        )

    if not bars:
        raise ValueError("No valid bars parsed from CSV")

    return bars
