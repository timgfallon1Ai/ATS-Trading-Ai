# ats/backtester/data_loader_polygon.py

import requests
import pandas as pd
import datetime as dt


class PolygonDataLoader:
    """
    Loads 1-minute historical bars from Polygon using the configured API key.
    """

    BASE_URL = (
        "https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/minute/{start}/{end}"
    )

    def __init__(self, api_key: str):
        self.api_key = api_key

    def load(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        url = self.BASE_URL.format(symbol=symbol, start=start, end=end)
        resp = requests.get(url, params={"adjusted": "true", "apiKey": self.api_key})
        data = resp.json()

        if "results" not in data:
            raise RuntimeError(f"Polygon returned no data for {symbol}: {data}")

        df = pd.DataFrame(data["results"])
        df["timestamp"] = df["t"] / 1000.0  # ms → seconds
        df.rename(
            columns={
                "o": "open",
                "h": "high",
                "l": "low",
                "c": "close",
                "v": "volume",
            },
            inplace=True,
        )

        return df[["timestamp", "open", "high", "low", "close", "volume"]]
