# ats/backtester2/bt_sanity.py

from __future__ import annotations

REQUIRED_ANALYST_METHODS = ["extract_features", "generate_signals"]

REQUIRED_AGGREGATOR_METHODS = ["combine"]

REQUIRED_RISK_METHODS = ["apply"]

REQUIRED_SIZER_METHODS = ["size"]

REQUIRED_ROUTER_METHODS = ["route"]

REQUIRED_EXECUTION_METHODS = ["execute"]

REQUIRED_SYNC_METHODS = ["apply_fills", "mark_to_market"]


def _require(obj, required: list[str], label: str):
    for m in required:
        if not hasattr(obj, m):
            raise AttributeError(f"{label} is missing required method: {m}")


def sanity_check_backtester(
    analyst,
    aggregator,
    risk,
    sizer,
    router,
    execution,
    sync,
):
    _require(analyst, REQUIRED_ANALYST_METHODS, "AnalystEngine")
    _require(aggregator, REQUIRED_AGGREGATOR_METHODS, "Aggregator")
    _require(risk, REQUIRED_RISK_METHODS, "RiskManager")
    _require(sizer, REQUIRED_SIZER_METHODS, "SizingBridge")
    _require(router, REQUIRED_ROUTER_METHODS, "TradeRouter")
    _require(execution, REQUIRED_EXECUTION_METHODS, "ExecutionBridge")
    _require(sync, REQUIRED_SYNC_METHODS, "PortfolioSync")

    return True
