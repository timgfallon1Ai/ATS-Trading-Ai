from __future__ import annotations
from typing import Dict, Any
from datetime import datetime

from ats.market_gateway.gateway import MarketGateway
from ats.analyst.hybrid_analyst import HybridAnalyst
from ats.aggregator.aggregator import Aggregator
from ats.risk_manager.risk_manager import RiskManager
from ats.trader.trader import Trader

from ats.orchestrator.log_writer import LogWriter


class ATSOrchestrator:
    """
    LIVE ATS ORCHESTRATOR (Z-11B)
    Pipeline:
        MarketGateway → HybridAnalyst → Aggregator → RiskManager → Trader
    """

    def __init__(self, starting_capital: float = 1000.0):
        self.market = MarketGateway()
        self.analyst = HybridAnalyst()
        self.aggregator = Aggregator()
        self.rm = RiskManager(base_capital=starting_capital)
        self.trader = Trader(starting_capital=starting_capital)

        # Logging layer
        self.log = LogWriter(log_dir="logs")

    # ------------------------------------------------------------
    def _ts(self) -> str:
        return datetime.utcnow().isoformat()

    # ------------------------------------------------------------
    def run_once(self) -> Dict[str, Any]:
        """
        Executes one full ATS cycle.
        """

        # --------------------------------------------------------
        # 1. Market data
        # --------------------------------------------------------
        market = self.market.fetch()
        self.log.write("market", {"snapshot": market})

        # --------------------------------------------------------
        # 2. Analyst (Hybrid AI + Strategy Ensemble)
        # --------------------------------------------------------
        analyst_out = self.analyst.generate(market)
        self.log.write("analyst", analyst_out)

        # --------------------------------------------------------
        # 3. Aggregator (S2 + U1)
        # --------------------------------------------------------
        allocs, strategy_meta = self.aggregator.build(analyst_out)
        self.log.write("aggregator", {"allocations": allocs})

        # --------------------------------------------------------
        # 4. Risk Manager (RM-MASTER)
        # --------------------------------------------------------
        rm_packets = self.rm.run_batch(
            allocations=allocs,
            features=analyst_out["features"],
            strategy_meta=strategy_meta,
        )

        # Log RM packets and governance events
        self.log.write("risk", rm_packets)

        gov_events = self.rm.gov_bus.flush()
        if gov_events:
            self.log.write_many(
                "governance",
                [e.__dict__ for e in gov_events],
            )

        # --------------------------------------------------------
        # 5. Trader
        # --------------------------------------------------------
        trade_out = self.trader.process_orders(rm_packets)
        self.log.write("trade", trade_out)

        return {
            "timestamp": self._ts(),
            "risk": rm_packets,
            "trades": trade_out,
        }
