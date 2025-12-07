from typing import Dict, List

import pyarrow.parquet as pq

from .normalization import normalize_bars
from .schema import Bar
from .validation import validate_bars


class UBFLoader:
    """Loads UBF (Unified Bar Format) data in parquet form.

    Structure:
    parquet/
        AAPL.parquet
        MSFT.parquet
        SPY.parquet
        ...

    Each file is expected to contain rows matching UBFSchema (v1.0).
    """

    def __init__(self, root: str):
        self.root = root

    def load_symbol(self, symbol: str) -> List[Bar]:
        path = f"{self.root}/{symbol}.parquet"

        table = pq.read_table(path)
        df = table.to_pandas()

        raw = df.to_dict(orient="records")
        validated = validate_bars(raw)
        normalized = normalize_bars(validated)
        return normalized

    def load_many(self, symbols: List[str]) -> Dict[str, List[Bar]]:
        out: Dict[str, List[Bar]] = {}

        for s in symbols:
            out[s] = self.load_symbol(s)

        return out
