class TwitterFeed:
    def get_sentiment(self, symbols: list[str]) -> dict[str, float]:
        return dict.fromkeys(symbols, 0.0)
