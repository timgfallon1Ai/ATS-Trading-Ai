# ats/backtester2/backtester_engine.py

from __future__ import annotations

from typing import Any, Dict

from ats.backtester2.backtest_config import BacktestConfig
from ats.backtester2.data_streamer import DataStreamer
from ats.backtester2.execution_bridge import ExecutionBridge
from ats.backtester2.ledger import Ledger
from ats.backtester2.portfolio_sim import PortfolioSimulator
from ats.backtester2.portfolio_sync import PortfolioSync
from ats.backtester2.position_book_bt import PositionBookBT
from ats.backtester2.sizer import SizingBridge
from ats.backtester2.trade_router import TradeRouter


class BacktesterEngine:
    """Master process for BT-2A (multi-symbol, portfolio-level).

    Pipeline per bar:
        1. Load next slices from DataStreamer
        2. Extract features via Analyst Engine
        3. Generate raw signals
        4. Combine via Aggregator
        5. Apply Risk Manager
        6. Size positions
        7. Convert to execution instructions
        8. Execute and receive fills
        9. PortfolioSync.apply_fills()
       10. MTM revaluation
       11. Ledger journal entry
    """

    def __init__(
        self,
        config: BacktestConfig,
        streamer: DataStreamer,
        analyst_engine,
        aggregator,
        risk_manager,
        execution_engine,
    ):
        self.config = config

        self.streamer = streamer
        self.analyst = analyst_engine
        self.aggregator = aggregator
        self.risk = risk_manager

        # Execution & routing
        self.trade_router = TradeRouter()
        self.sizer = SizingBridge(config)

        self.execution_bridge = ExecutionBridge(engine=execution_engine)

        # State objects
        self.position_book = PositionBookBT()
        self.portfolio = PortfolioSimulator(config=config)
        self.ledger = Ledger()

        self.sync = PortfolioSync(
            position_book=self.position_book, portfolio_sim=self.portfolio
        )

        self.results: Dict[str, Any] = {}

    # ---------------------------------------------------------
    # MAIN LOOP
    # ---------------------------------------------------------
    def run(self) -> Dict[str, Any]:
        iterator = self.streamer.iter_bars()

        prev_slice = None
        for timestamp, slices in iterator:
            # 1) Analyst: features + signals
            features = self.analyst.extract_features(slices)
            signals = self.analyst.generate_signals(features)

            # 2) Aggregator
            combined = self.aggregator.combine(signals, features)

            # 3) Risk Manager
            risk_adjusted = self.risk.apply(
                combined_signals=combined,
                features=features,
                timestamp=timestamp,
                portfolio=self.position_book.positions,
            )

            # 4) Sizing
            sized_orders = self.sizer.size(
                risk_adjusted=risk_adjusted,
                positions=self.position_book.positions,
                equity=self.portfolio.equity,
            )

            # 5) Routing
            exec_instructions = self.trade_router.route(sized_orders)

            # 6) Execution
            fills = self.execution_bridge.execute(
                instructions=exec_instructions,
                current_bar=slices,
                next_bar=prev_slice,
                timestamp=timestamp,
            )

            # 7) Sync
            self.sync.apply_fills(fills)

            # 8) MTM
            self.sync.mark_to_market(slices, timestamp)

            # 9) Ledger entry
            self.ledger.record(
                timestamp=timestamp,
                fills=fills,
                equity=self.portfolio.equity,
                positions=self.position_book.positions,
            )

            prev_slice = slices

        # 10) Final stats
        self.results = self.ledger.finalize(equity=self.portfolio.equity)
        return self.results
