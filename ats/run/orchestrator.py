from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, TYPE_CHECKING

from ats.backtester2.run import run_backtest as bt2_run_backtest
from ats.orchestrator.log_writer import LogWriter

if TYPE_CHECKING:
    from ats.backtester2.engine import BacktestResult


@dataclass(frozen=True)
class BacktestRunConfig:
    symbol: str
    days: int = 200
    enable_risk: bool = True


class RuntimeOrchestrator:
    """Unified orchestrator used by `python -m ats.run`.

    Currently: backtest-first (Backtester2).
    Later: paper/live trading loops can be added behind the same interface.
    """

    def __init__(self, log: LogWriter) -> None:
        self._log = log

    @property
    def log(self) -> LogWriter:
        return self._log

    def run_backtest(self, cfg: BacktestRunConfig) -> "BacktestResult":
        self._log.emit(
            "session_start",
            {
                "mode": "backtest",
                "symbol": cfg.symbol,
                "days": cfg.days,
                "risk_enabled": cfg.enable_risk,
            },
        )

        status = "success"
        result: Optional["BacktestResult"] = None

        try:
            result = bt2_run_backtest(
                symbol=cfg.symbol,
                days=cfg.days,
                enable_risk=cfg.enable_risk,
            )

            summary: Dict[str, Any] = {
                "symbol": result.config.symbol,
                "days": cfg.days,
                "trades": len(result.trade_history),
                "risk_evaluations": len(result.risk_decisions),
            }

            if result.final_portfolio is not None:
                summary["final_portfolio"] = result.final_portfolio

            if result.risk_decisions:
                blocked = sum(len(d.rejected_orders) for d in result.risk_decisions)
                summary["risk_blocked_orders"] = blocked

            self._log.emit("backtest_complete", summary)
            return result

        except Exception as exc:  # noqa: BLE001
            status = "error"
            self._log.exception(
                "session_error",
                {
                    "mode": "backtest",
                    "symbol": cfg.symbol,
                    "days": cfg.days,
                    "risk_enabled": cfg.enable_risk,
                },
                exc=exc,
            )
            raise

        finally:
            self._log.emit(
                "session_end",
                {
                    "mode": "backtest",
                    "symbol": cfg.symbol,
                    "status": status,
                    "had_result": result is not None,
                },
            )

    def run_live(self) -> None:
        raise NotImplementedError(
            "Live runtime not implemented yet. Use `ats.run backtest` for now."
        )


# Backwards-compat alias (if any older imports reference Orchestrator)
Orchestrator = RuntimeOrchestrator
