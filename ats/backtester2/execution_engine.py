# ats/backtester2/execution_engine.py

from __future__ import annotations

from typing import Any, Dict, List

from ats.backtester2.latency_model import LatencyModel
from ats.backtester2.order_book import OrderBook
from ats.backtester2.slippage_model import SlippageModel


class ExecutionEngine:
    """Deterministic backtest execution engine using:
        - OrderBook (micro, best bid/ask)
        - LatencyModel (delayed execution)
        - SlippageModel (price adjustment)

    Output: List of canonical fill dictionaries.
    """

    def __init__(
        self,
        order_book: OrderBook,
        latency: LatencyModel,
        slippage: SlippageModel,
        fill_on: str = "next_bar_open",  # or "same_bar_open"
    ):
        self.order_book = order_book
        self.latency = latency
        self.slippage = slippage
        self.fill_on = fill_on

    # ------------------------------------------------------------
    # Execute batch of sized trade instructions
    # ------------------------------------------------------------

    def execute(
        self,
        instructions: List[Dict[str, Any]],
        current_bar: Dict[str, Any],
        next_bar: Dict[str, Any] | None,
        timestamp: int,
    ) -> List[Dict[str, Any]]:
        """instructions: [
            {"symbol": "AAPL", "target_qty": 42, "reason": "...", ...}
        ]

        current_bar: { symbol: { "open": float, "high": float, ... } }
        next_bar:    same as above (needed for next-bar-open fills)
        """
        fills: List[Dict[str, Any]] = []

        for instr in instructions:
            symbol = instr["symbol"]
            target_qty = instr["target_qty"]
            if target_qty == 0:
                continue

            # Determine fill bar
            bar = next_bar if self.fill_on == "next_bar_open" else current_bar
            if bar is None or symbol not in bar:
                continue

            base_price = bar[symbol]["open"]

            # Apply simulated latency
            exec_ts = timestamp + self.latency.delay_milliseconds() // 1000

            # Pull microstructure bid/ask spread
            best_bid, best_ask = self.order_book.get_best_quotes(symbol)

            mid = (best_bid + best_ask) / 2
            raw_price = mid

            # Apply slippage
            final_price = self.slippage.apply(
                symbol=symbol,
                qty=target_qty,
                price=raw_price,
                best_bid=best_bid,
                best_ask=best_ask,
            )

            fills.append(
                {
                    "symbol": symbol,
                    "qty": target_qty,
                    "price": final_price,
                    "timestamp": exec_ts,
                }
            )

        return fills
