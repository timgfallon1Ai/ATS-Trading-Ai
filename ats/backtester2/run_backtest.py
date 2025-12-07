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
