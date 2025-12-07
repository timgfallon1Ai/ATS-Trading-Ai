# ats/backtester2/run_bt.py

from __future__ import annotations

from ats.aggregator.aggregator import Aggregator

# External ATS subsystems
from ats.analyst.analyst_engine import AnalystEngine
from ats.backtester2.backtest_config import BacktestConfig
from ats.backtester2.backtester_engine import BacktesterEngine
from ats.backtester2.data_streamer import DataStreamer
from ats.backtester2.execution_engine import ExecutionEngine
from ats.risk_manager.risk_manager import RiskManager


def run_backtest(parquet_path: str, config_overrides: dict | None = None):
    """CLI-friendly wrapper for running a full backtest."""
    config = BacktestConfig(**(config_overrides or {}))

    streamer = DataStreamer(
        parquet_path=parquet_path,
        symbols=config.symbols,
        start=config.start,
        end=config.end,
    )

    analyst = AnalystEngine(config=config)
    aggregator = Aggregator(config=config)
    risk = RiskManager(config=config)
    execution_engine = ExecutionEngine(config=config)

    engine = BacktesterEngine(
        config=config,
        streamer=streamer,
        analyst_engine=analyst,
        aggregator=aggregator,
        risk_manager=risk,
        execution_engine=execution_engine,
    )

    results = engine.run()

    print("=== BACKTEST COMPLETE ===")
    print(f"Final equity: {results.get('final_equity')}")
    print(f"Sharpe: {results.get('sharpe')}")
    print(f"Max Drawdown: {results.get('max_drawdown')}")
    print()

    return results
