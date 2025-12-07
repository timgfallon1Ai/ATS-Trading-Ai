from __future__ import annotations

from typing import Any, Dict


class Orchestrator:
    """The unified trading orchestrator:
    - Runs the ingestion layer
    - Feeds analyst
    - Feeds risk manager
    - Feeds aggregator
    - Sends intents to trader
    - Sends results to dashboard
    - Maintains posture/state
    """

    def __init__(self, registry):
        self.reg = registry

    # -----------------------------------------------------------
    # ONE COMPLETE SYSTEM TICK
    # -----------------------------------------------------------
    def step(self):

        # ----------------------------
        # 1) INGEST AND MERGE BARS
        # ----------------------------
        ubf = self.reg["ubf"]
        merged_bars = ubf.fetch()  # {sym: merged_bar_dict}

        # ----------------------------
        # 2) ANALYST SIGNALS
        # ----------------------------
        analyst = self.reg["analyst"]
        signals_by_symbol: Dict[str, Any] = {}
        for sym, bar in merged_bars.items():
            signals_by_symbol[sym] = analyst.generate(bar)

        # ----------------------------
        # 3) RISK MANAGER
        # ----------------------------
        rm = self.reg["risk"]
        risk_filtered = rm.apply(signals_by_symbol)

        # ----------------------------
        # 4) AGGREGATOR
        # ----------------------------
        agg = self.reg["aggregator"]
        intents = agg.process_batch(merged_bars, risk_filtered)

        # ----------------------------
        # 5) TRADER EXECUTION
        # ----------------------------
        trader = self.reg["trader"]
        trader.execute_intents(intents, merged_bars)

        # ----------------------------
        # 6) EQUITY / POSTURE UPDATE
        # ----------------------------
        posture = self.reg["posture"]
        equity = self.reg["equity"]

        latest_prices = {s: merged_bars[s]["close"] for s in merged_bars}
        equity_value = equity.total(latest_prices)
        posture.update_equity(equity_value)

        # ----------------------------
        # 7) DASHBOARD FEED
        # ----------------------------
        dashboard = self.reg["dashboard"]
        dashboard.push(
            {
                "equity": equity_value,
                "posture": posture.state,
                "positions": trader.book.positions,
                "last_intents": intents,
            }
        )
