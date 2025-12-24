from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from ats.backtester2.artifacts import write_backtest_artifacts
from ats.backtester2.run import run_backtest as bt2_run_backtest
from ats.orchestrator.log_writer import LogWriter


def create_run_id(prefix: str = "run") -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{prefix}-{ts}-{uuid.uuid4().hex[:8]}"


@dataclass
class BacktestRunConfig:
    symbol: str
    days: int = 50
    strategy: str = "ma"
    enable_risk: bool = True
    strategy_names: Optional[List[str]] = None
    max_position_frac: float = 0.20
    csv: Optional[str] = None
    log_dir: Path = Path("logs")
    run_id: Optional[str] = None


class RuntimeOrchestrator:
    """
    Runtime orchestrator for `python -m ats.run backtest`.

    Responsibilities required by Phase 14:
      - create run dir + events.jsonl
      - execute backtest
      - write artifacts into run dir:
          equity_curve.csv, trades.csv, metrics.json
    """

    def __init__(
        self, log_dir: Path = Path("logs"), run_id: Optional[str] = None
    ) -> None:
        self.log_dir = Path(log_dir)
        self.run_id = run_id
        self.log: Optional[LogWriter] = None

    def run_backtest(self, cfg: BacktestRunConfig):
        run_id = cfg.run_id or self.run_id or create_run_id("backtest")
        cfg.run_id = run_id

        log = LogWriter(log_dir=cfg.log_dir, run_id=run_id)
        self.log = log

        log.event(
            "run_start",
            meta={
                "kind": "backtest",
                "run_id": run_id,
                "symbol": cfg.symbol,
                "days": cfg.days,
                "strategy": cfg.strategy,
                "enable_risk": cfg.enable_risk,
            },
        )

        result = bt2_run_backtest(
            symbol=cfg.symbol,
            days=cfg.days,
            enable_risk=cfg.enable_risk,
            strategy=cfg.strategy,
            strategy_names=cfg.strategy_names,
            max_position_frac=cfg.max_position_frac,
            csv=cfg.csv,
        )

        # Write required run artifacts into the SAME run directory as events.jsonl
        paths = write_backtest_artifacts(
            portfolio_history=getattr(result, "portfolio_history", []) or [],
            trade_history=getattr(result, "trade_history", []) or [],
            out_dir=log.path,
        )

        log.event("artifacts_written", meta={"paths": [str(p) for p in paths]})
        log.event("run_end", meta={"run_id": run_id})
        return result
