# ats/backtester2/run_backtest.py

from __future__ import annotations

from typing import Any, Dict

from .engine import BT2Engine


def run_backtest(
    data: Dict[int, Dict[str, Dict[str, float]]], dispatcher
) -> Dict[str, Any]:
    """External entry point for BT-2A.
    Provides the data + dispatcher and returns the final report.
    """
    engine = BT2Engine(
        dispatcher=dispatcher,
        initial_equity=1000.0,
        trace_enabled=False,
        snapshot_enabled=False,
    )

    results = engine.run(data)
    return results


if __name__ == "__main__":
    # Example placeholder
    print("Backtester runner is not invoked directly — use run_backtest().")

log_path = (
    getattr(self.log, "path", None)
    or getattr(self.log, "events_path", None)
    or getattr(self.log, "log_dir", None)
)
run_dir = Path(log_path) if log_path is not None else Path("logs")
if run_dir.suffix:  # events.jsonl
    run_dir = run_dir.parent

artifact_paths = write_backtest_artifacts(
    portfolio_history=res.portfolio_history or [],
    trade_history=res.trade_history or [],
    out_dir=run_dir,
)

self.log.event(
    "artifacts_written",
    meta={"paths": [str(p) for p in artifact_paths]},
)
