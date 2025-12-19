from __future__ import annotations

import inspect
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ats.run.service_registry import ServiceRegistry


@dataclass(frozen=True)
class BacktestRequest:
    """Parameters for a backtest run."""

    symbol: str
    days: int = 200
    starting_cash: float = 100000.0
    no_risk: bool = False


class Orchestrator:
    """Unified runtime orchestrator (backtest-first).

    Today this module primarily provides a stable entrypoint and an execution
    surface to:
      - run Backtester2 deterministically,
      - emit JSONL logs (via ats.orchestrator.log_writer.LogWriter).

    Later phases can extend this to PAPER/LIVE loops without changing the
    backtest contract.
    """

    def __init__(self, registry: ServiceRegistry, run_id: Optional[str] = None):
        self._reg = registry
        self._run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    @property
    def run_id(self) -> str:
        return self._run_id

    def _emit(self, record_type: str, payload: Dict[str, Any]) -> None:
        logger = self._reg.get("log")
        if logger is None:
            return
        try:
            logger.write(record_type, payload)
        except Exception:
            # Logging must never break trading/backtesting.
            return

    def run_backtest(self, req: BacktestRequest) -> Any:
        """Run a Backtester2 job and emit start/end events."""

        self._emit(
            "session_start",
            {
                "run_id": self._run_id,
                "mode": "BACKTEST",
                "symbol": req.symbol,
                "days": req.days,
                "starting_cash": req.starting_cash,
                "risk_enabled": (not req.no_risk),
            },
        )

        from ats.backtester2 import run as bt_run  # local import to avoid cycles

        if not hasattr(bt_run, "run_backtest"):
            raise RuntimeError("ats.backtester2.run.run_backtest() not found")

        fn = bt_run.run_backtest
        sig = inspect.signature(fn)

        kwargs: Dict[str, Any] = {}
        if "symbol" in sig.parameters:
            kwargs["symbol"] = req.symbol
        if "days" in sig.parameters:
            kwargs["days"] = int(req.days)

        # Support a few likely naming conventions without forcing one.
        if "starting_cash" in sig.parameters:
            kwargs["starting_cash"] = float(req.starting_cash)
        elif "starting_capital" in sig.parameters:
            kwargs["starting_capital"] = float(req.starting_cash)
        elif "capital" in sig.parameters:
            kwargs["capital"] = float(req.starting_cash)

        if "no_risk" in sig.parameters:
            kwargs["no_risk"] = bool(req.no_risk)
        elif "risk_enabled" in sig.parameters:
            kwargs["risk_enabled"] = bool(not req.no_risk)
        elif "enable_risk" in sig.parameters:
            kwargs["enable_risk"] = bool(not req.no_risk)

        result = fn(**kwargs)

        summary = self._summarize_backtest_result(result)
        self._emit(
            "session_end",
            {
                "run_id": self._run_id,
                "mode": "BACKTEST",
                "symbol": req.symbol,
                "summary": summary,
            },
        )
        return result

    def _summarize_backtest_result(self, result: Any) -> Dict[str, Any]:
        """Best-effort result summary (robust to minor schema changes)."""

        trade_hist = getattr(result, "trade_history", None)
        if trade_hist is None:
            trade_hist = getattr(result, "trades", None)

        final_pf = getattr(result, "final_portfolio", None)
        if final_pf is None:
            final_pf = getattr(result, "portfolio", None)

        cfg = getattr(result, "config", None)
        symbol = getattr(cfg, "symbol", None) if cfg is not None else None

        return {
            "symbol": symbol,
            "trades": len(trade_hist) if isinstance(trade_hist, list) else None,
            "final_portfolio": final_pf,
        }
