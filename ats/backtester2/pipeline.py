from typing import Any, Dict

from ats.backtester2.context import BacktestContext
from ats.backtester2.live_bindings import LiveBindings


class BacktestPipeline:
    """Single-bar deterministic processing pipeline.

    Order:
        1) Analyst: extract features
        2) Analyst: generate signals
        3) Aggregator: combine signals
        4) Risk Manager: enforce posture
        5) Trader: generate executions
        6) Trader: update portfolio
        7) Journaling: equity, positions, trades
    """

    def __init__(self, ctx: BacktestContext, bindings: LiveBindings):
        self.ctx = ctx
        self.bindings = bindings

    def process_bar(self, bar: Dict[str, Any], timestamp: int) -> None:
        # 1 — Extract features
        features = self.bindings.extract_features(bar)

        # 2 — Strategy signals
        signals = self.bindings.generate_signals(features)

        # 3 — Aggregation
        combined = self.ctx.aggregator.combine(signals=signals, features=features)

        # 4 — Risk manager
        rm_adjusted = self.ctx.risk_manager.apply(combined)

        # 5 — Trader: simulate fills
        executions = self.ctx.trader.execute(
            timestamp=timestamp, target_positions=rm_adjusted
        )

        # Log executions
        for e in executions:
            self.ctx.exec_writer.append(e)

        # 6 — Update portfolio
        portfolio_state = self.ctx.trader.update_portfolio(
            timestamp=timestamp, executions=executions
        )

        # 7 — Journaling
        self.ctx.position_journal.append(portfolio_state)

        # 8 — Equity curve
        self.ctx.equity_writer.append(
            {"timestamp": timestamp, "equity": portfolio_state["equity"]}
        )
