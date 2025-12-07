from typing import Any, Dict

import requests

from ats.config.config_loader import Config


class PolygonFeed:
    """Polygon Live Market Data
    - Last trade price
    - Volume
    - Timestamp
    """

    def __init__(self):
        self.key = Config().polygon_key()

    def get_price(self, symbol: str) -> Dict[str, Any]:
        url = f"https://api.polygon.io/v2/last/trade/{symbol}?apiKey={self.key}"
        r = requests.get(url, timeout=3).json()

        price = float(r["results"]["p"])
        ts = r["results"]["t"]

        return {
            "price": price,
            "timestamp": ts,
            "source": "polygon",
            "raw": r,
        }
