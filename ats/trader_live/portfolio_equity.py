from __future__ import annotations

from typing import Dict

from ats.trader_live.live_position_book import LivePositionBook


class PortfolioEquity:
    """Tracks total equity based on:
    - cash
    - unrealized PnL
    """

    def __init__(self, starting_cash: float = 1000.0):
        self.cash = starting_cash
        self.book = None  # hooked up later

    def attach_book(self, book: LivePositionBook):
        self.book = book

    def update_after_fill(
        self, symbol: str, fill_price: float, size_delta: float
    ) -> None:
        cost = fill_price * size_delta * -1
        self.cash += cost

    def total(self, latest_prices: Dict[str, float]) -> float:
        unreal = 0.0
        for sym, pos in self.book.positions.items():
            if pos.size != 0:
                m = latest_prices.get(sym, pos.avg_price)
                unreal += pos.size * (m - pos.avg_price)
        return self.cash + unreal
