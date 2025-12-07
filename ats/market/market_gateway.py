from typing import Any, Dict

from ats.market.providers.benzinga_feed import BenzingaNews
from ats.market.providers.ibkr_feed import IBKRFeed
from ats.market.providers.polygon_feed import PolygonFeed
from ats.market.providers.twitter_feed import TwitterFeed


class MarketGateway:
    """MG-3 Unified Market Gateway (Option A)
    Normalizes:
        - Polygon (primary)
        - IBKR (secondary)
        - Benzinga (news)
        - Twitter (sentiment)
    """

    def __init__(self):
        self.poly = PolygonFeed()
        self.ibkr = IBKRFeed()
        self.benz = BenzingaNews()
        self.tw = TwitterFeed()

    # ------------------------------------------------------------
    # Unified price lookup
    # ------------------------------------------------------------
    def get_price(self, symbol: str) -> Dict[str, Any]:
        try:
            return self.poly.get_price(symbol)
        except Exception:
            return self.ibkr.get_price(symbol)

    # ------------------------------------------------------------
    # Unified bundle for Analyst → Aggregator → RM
    # ------------------------------------------------------------
    def get_bundle(self, symbol: str) -> Dict[str, Any]:
        price = self.get_price(symbol)
        news = self.benz.get_news(symbol)
        tweets = self.tw.search(symbol)

        return {
            "symbol": symbol,
            "price": price["price"],
            "timestamp": price["timestamp"],
            "volume": price["raw"].get("s", None),
            "sources": {
                "polygon": price,
                "benzinga": news,
                "twitter": tweets,
            },
        }

    # ------------------------------------------------------------
    # For Trader
    # ------------------------------------------------------------
    def get_all_prices(self, symbols: list[str]) -> Dict[str, float]:
        out = {}
        for s in symbols:
            out[s] = float(self.get_price(s)["price"])
        return out
