from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, TYPE_CHECKING

from ats.backtester2.run import run_backtest as bt2_run_backtest
from ats.core.kill_switch import read_kill_switch_status
from ats.orchestrator.log_writer import LogWriter

if TYPE_CHECKING:
    from ats.backtester2.engine import BacktestResult


@dataclass(frozen=True)
class BacktestRunConfig:
    symbol: str
    days: int = 200
    enable_risk: bool = True


class RuntimeOrchestrator:
    """
    Unified orchestrator used by `python -m ats.run`.

    Phase9.3:
      - Logs kill-switch status at session start
      - Backtest loop honors kill-switch inside BacktestEngine (checked every bar)
    """

    def __init__(self, log: LogWriter) -> None:
        self._log = log

    @property
    def log(self) -> LogWriter:
        return self._log

    def run_backtest(self, cfg: BacktestRunConfig) -> "BacktestResult":
        ks = read_kill_switch_status()

        self._log.emit(
            "session_start",
            {
                "mode": "backtest",
                "symbol": cfg.symbol,
                "days": cfg.days,
                "risk_enabled": cfg.enable_risk,
                "kill_switch": {
                    "engaged": ks.engaged,
                    "forced_by_env": ks.forced_by_env,
                    "file_exists": ks.file_exists,
                    "path": str(ks.path),
                    "enabled_at": ks.enabled_at,
                    "reason": ks.reason,
                },
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
                "symbol": cfg.symbol,
                "days": cfg.days,
                "trades": len(result.trade_history),
                "risk_evaluations": len(result.risk_decisions),
            }
            if result.final_portfolio is not None:
                summary["final_portfolio"] = result.final_portfolio

            self._log.emit("backtest_complete", summary)
            return result

        except Exception as exc:  # noqa: BLE001
            status = "error"
            self._log.exception(
                "session_error",
                {"mode": "backtest", "symbol": cfg.symbol, "days": cfg.days},
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
        ks = read_kill_switch_status()
        if ks.engaged:
            self._log.emit(
                "kill_switch_block_live",
                {
                    "path": str(ks.path),
                    "reason": ks.reason,
                    "enabled_at": ks.enabled_at,
                },
            )
            raise SystemExit(f"Kill switch engaged at {ks.path}. Live run blocked.")

        raise NotImplementedError(
            "Live runtime not implemented yet. Use `ats.run backtest` for now."
        )


Orchestrator = RuntimeOrchestrator
