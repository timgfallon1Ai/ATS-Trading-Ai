# ats/backtester/data_loader_benzinga.py

import requests
import datetime as dt

class BenzingaNewsLoader:
    """
    Loads timestamped news events for a symbol.
    Only necessary for strategies using sentiment.
    """

    BASE_URL = "https://api.benzinga.com/api/v2/news"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def load(self, symbol: str, start: str, end: str):
        resp = requests.get(
            self.BASE_URL,
            params={
                "token": self.api_key,
                "symbols": symbol,
                "published_since": start,
                "published_until": end,
            }
        )
        data = resp.json()
        events = []

        for n in data:
            ts = dt.datetime.fromisoformat(n["created"]).timestamp()
            events.append({
                "timestamp": ts,
                "headline": n["title"],
                "summary": n.get("description", ""),
                "sentiment": n.get("sentiment", {}).get("value", 0.0),
            })

        return events
