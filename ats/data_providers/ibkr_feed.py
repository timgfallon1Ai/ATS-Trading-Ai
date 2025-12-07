class IBKRFeed:
    def get_price(self, symbol: str) -> float:
        return 0.0  # stub

    def get_prices(self, symbols: list[str]) -> dict[str, float]:
        return dict.fromkeys(symbols, 0.0)
