# ats/backtester/backtester.py

from __future__ import annotations
from typing import Dict, Any, List
import datetime as dt

from ats.backtester.event_queue import EventQueue
from ats.backtester.execution_context import ExecutionContext

class Backtester:
    """
    Z-12 Backtester (L2 Output)
    Event-driven pipeline:
        BAR → Analyst → Aggregator → RM-MASTER → Trader → Portfolio
        NEWS → Analyst (if strategy uses it)
    """

    def __init__(self, analyst, aggregator, rm_master, trader):
        self.ctx = ExecutionContext(analyst, aggregator, rm_master, trader)
        self.queue = EventQueue()

    # ----------------------------------------------------
    def load_data(self, bars_df, news_events: List[Dict]):
        """
        Convert OHLCV bars + news into queue events.
        bars_df: DataFrame with timestamp column
        news_events: list of {timestamp, sentiment, headline}
        """

        for _, row in bars_df.iterrows():
            self.queue.push(
                timestamp=float(row["timestamp"]),
                type="BAR",
                data=dict(row),
            )

        for ev in news_events:
            self.queue.push(
                timestamp=ev["timestamp"],
                type="NEWS",
                data=ev,
            )

    # ----------------------------------------------------
    def run(self):
        """
        Main simulation loop.
        """

        while not self.queue.empty():
            ev = self.queue.pop()

            if ev.type == "BAR":
                self._handle_bar(ev.data)
            elif ev.type == "NEWS":
                self._handle_news(ev.data)

        return {
            "portfolio": self.ctx.portfolio_history,
            "trades": self.ctx.trade_history,
            "rm_packets": self.ctx.rm_packets,
            "signals": self.ctx.signals,
            "allocations": self.ctx.allocations,
        }

    # ----------------------------------------------------
    def _handle_news(self, news):
        sentiment = news.get("sentiment", 0.0)
        # Analyst engine can ingest this if used
        try:
            self.ctx.analyst.ingest_news(news)
        except AttributeError:
            pass

    # ----------------------------------------------------
    def _handle_bar(self, bar):
        prices = {"close": bar["close"], "open": bar["open"]}

        # 1) Analyst → signals + features
        analyst_out = self.ctx.analyst.run(bar)
        self.ctx.signals.append(analyst_out)

        # 2) Aggregator → allocations
        alloc = self.ctx.aggregator.generate_allocations(analyst_out)
        self.ctx.allocations.append(alloc)

        # 3) RM → packets
        rm_packets = self.ctx.rm_master.run_batch(alloc)
        self.ctx.rm_packets.append(rm_packets)

        # 4) Trader → fills + portfolio update
        trade_out = self.ctx.trader.process_orders(rm_packets)
        self.ctx.trade_history.append(trade_out)

        # 5) Portfolio snapshot
        snapshot = trade_out["portfolio"]
        self.ctx.snapshot(snapshot)
