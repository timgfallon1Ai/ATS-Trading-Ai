from typing import Any, Dict

import requests

from ats.config.config_loader import Config


class TwitterFeed:
    """Pulls tweets for news-sentiment strategy
    Uses Basic tier (bearer token)
    """

    def __init__(self):
        self.token = Config().twitter_token()

    def search(self, query: str, limit: int = 20) -> Dict[str, Any]:
        url = "https://api.twitter.com/2/tweets/search/recent"
        headers = {"Authorization": f"Bearer {self.token}"}

        params = {"query": query, "max_results": limit}

        r = requests.get(url, headers=headers, params=params).json()

        return {
            "query": query,
            "count": len(r.get("data", [])),
            "items": r.get("data", []),
            "source": "twitter",
        }
