from dataclasses import dataclass
from typing import Any, Dict

from ats.aggregator.aggregator import Aggregator
from ats.analyst.analyst_engine import AnalystEngine
from ats.backtester2.io.equity_curve_writer import EquityCurveWriter
from ats.backtester2.io.execution_log_writer import ExecutionLogWriter
from ats.backtester2.io.manifest import BacktestManifest
from ats.backtester2.io.position_journal import PositionJournal
from ats.backtester2.io.results_writer import ResultsWriter
from ats.risk_manager.risk_manager import RiskManager
from ats.trader.trader import Trader


@dataclass
class BacktestContext:
    analyst: AnalystEngine
    aggregator: Aggregator
    risk_manager: RiskManager
    trader: Trader

    manifest: BacktestManifest
    results: ResultsWriter
    equity_writer: EquityCurveWriter
    exec_writer: ExecutionLogWriter
    position_journal: PositionJournal

    config: Dict[str, Any]
