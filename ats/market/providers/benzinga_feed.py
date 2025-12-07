from typing import Any, Dict

import requests

from ats.config.config_loader import Config


class BenzingaNews:
    """Benzinga Free Tier News Feed
    - Headlines only (good for sentiment bootstrapping)
    """

    def __init__(self):
        self.key = Config().benzinga_key()

    def get_news(self, symbol: str) -> Dict[str, Any]:
        url = (
            f"https://api.benzinga.com/api/v2/news?"
            f"token={self.key}&symbols={symbol}&display_output=abstract"
        )

        r = requests.get(url, timeout=3).json()

        return {
            "symbol": symbol,
            "count": len(r),
            "items": r,
            "source": "benzinga",
        }
