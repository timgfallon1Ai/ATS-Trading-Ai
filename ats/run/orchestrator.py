from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ats.backtester2.run import run_backtest as bt2_run_backtest
from ats.core.kill_switch import kill_switch_status
from ats.orchestrator.log_writer import LogWriter


def _as_dict(obj: Any) -> Dict[str, Any]:
    """
    Best-effort conversion of status-ish objects into JSONable dicts.
    """
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj

    to_dict = getattr(obj, "to_dict", None)
    if callable(to_dict):
        try:
            v = to_dict()
            if isinstance(v, dict):
                return v
        except Exception:
            pass

    if hasattr(obj, "__dict__"):
        try:
            return dict(obj.__dict__)
        except Exception:
            pass

    return {"value": str(obj)}


@dataclass(frozen=True)
class BacktestRunConfig:
    symbol: str = "AAPL"
    days: int = 200
    enable_risk: bool = True

    # Backtester2 passthroughs
    csv: Optional[str] = None
    strategy: str = "ma"
    strategy_names: Optional[List[str]] = None
    max_position_frac: float = 0.2


@dataclass(frozen=True)
class LiveRunConfig:
    symbol: Optional[str] = None
    paper: bool = True


class RuntimeOrchestrator:
    """
    Lightweight runtime wrapper that:
      - records run_start/run_end events to JSONL
      - calls Backtester2 programmatically
    """

    BacktestRunConfig = BacktestRunConfig
    LiveRunConfig = LiveRunConfig

    def __init__(self, log: LogWriter) -> None:
        self.log = log

    def run_backtest(self, cfg: BacktestRunConfig):
        st = kill_switch_status()
        self.log.event("session_status", meta={"kill_switch": _as_dict(st)})

        self.log.event(
            "run_start",
            meta={
                "mode": "backtest",
                "symbol": cfg.symbol,
                "days": cfg.days,
                "enable_risk": cfg.enable_risk,
                "csv": cfg.csv,
                "strategy": cfg.strategy,
                "strategy_names": cfg.strategy_names,
                "max_position_frac": cfg.max_position_frac,
            },
        )

        try:
            res = bt2_run_backtest(
                symbol=cfg.symbol,
                days=cfg.days,
                enable_risk=cfg.enable_risk,
                csv=cfg.csv,
                strategy=cfg.strategy,
                strategy_names=cfg.strategy_names,
                max_position_frac=cfg.max_position_frac,
            )
            self.log.event("run_end", meta={"mode": "backtest", "status": "ok"})
            return res
        except Exception as e:
            self.log.event(
                "run_end",
                meta={"mode": "backtest", "status": "error", "error": str(e)},
            )
            raise

    def run_live(self, cfg: Optional[LiveRunConfig] = None) -> None:
        _ = cfg or LiveRunConfig()
        self.log.event("run_start", meta={"mode": "live"})
        self.log.event("run_end", meta={"mode": "live", "status": "noop"})
        print("Live mode is not implemented yet.")
