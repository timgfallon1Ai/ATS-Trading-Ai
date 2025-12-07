from __future__ import annotations

from typing import List

from ats.live_aggregator.live_aggregator_engine import LiveAggregatorEngine
from ats.live_risk.posture_sync import PostureSync

from .live_execution_engine import LiveExecutionEngine
from .live_market_data import LiveMarketData
from .live_order_router import LiveOrderRouter
from .live_position_book import LivePositionBook
from .order_converter import OrderConverter
from .portfolio_equity import PortfolioEquity


class TradeLoop:
    """Full live trading pipeline:

    market → merged →
    analyst → signals →
    risk → intents →
    sizing/allocation →
    orders → fills → equity update

    """

    def __init__(
        self,
        symbols: List[str],
        analyst_fn,
        aggregator: LiveAggregatorEngine,
        md: LiveMarketData,
        execution: LiveExecutionEngine,
        router: LiveOrderRouter,
        converter: OrderConverter,
        book: LivePositionBook,
        equity: PortfolioEquity,
        posture: PostureSync,
    ):
        self.symbols = symbols
        self.analyst_fn = analyst_fn
        self.agg = aggregator
        self.md = md
        self.exec = execution
        self.router = router
        self.conv = converter
        self.book = book
        self.equity = equity
        self.posture = posture

    # ----------------------------------------------------
    # ONE FULL LIVE TICK
    # ----------------------------------------------------
    def step(self) -> None:
        merged = {}
        latest_prices = {}

        # live market snapshots
        for sym in self.symbols:
            quote = self.md.get(sym)
            merged[sym] = quote
            latest_prices[sym] = quote["close"]

        # analyst signals
        signals = self.analyst_fn(merged)

        # aggregator → final intents
        trade_intents = self.agg.process(
            merged[list(merged.keys())[0]], signals  # primary symbol routing
        )

        # trade execution
        for intent in trade_intents:
            order = self.conv.convert(intent)
            routed = self.router.send(order)
            fill = self.exec.execute(order, merged[order["symbol"]])

            self.book.apply_fill(fill["symbol"], fill["size_delta"], fill["price"])

            # equity update
            self.equity.update_after_fill(
                fill["symbol"], fill["price"], fill["size_delta"]
            )

        # update posture ($1k → $2k rule)
        total_eq = self.equity.total(latest_prices)
        self.posture.update_equity(total_eq)
