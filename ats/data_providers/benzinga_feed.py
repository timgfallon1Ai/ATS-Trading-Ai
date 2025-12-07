class BenzingaFeed:
    def get_news(self, symbols: list[str]) -> list[dict]:
        return []

    def get_sentiment(self, symbols: list[str]) -> dict[str, float]:
        return dict.fromkeys(symbols, 0.0)
