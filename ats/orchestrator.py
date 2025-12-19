from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ats.run.boot import BootConfig, boot_system
from ats.run.orchestrator import BacktestRequest


class ATSOrchestrator:
    """Compatibility orchestrator.

    Historically this repo had a separate `ats.orchestrator`. The canonical runtime
    entrypoint is now:

        python -m ats.run backtest --symbol AAPL --days 200

    This class remains as a thin wrapper so older scripts (like repo-root run.py)
    can continue to work.
    """

    def __init__(
        self,
        starting_capital: float = 100000.0,
        log_dir: str = "logs",
        run_id: Optional[str] = None,
    ):
        self._starting_capital = float(starting_capital)
        self._log_dir = str(log_dir)
        self._reg = boot_system(BootConfig(log_dir=self._log_dir, run_id=run_id))
        self._orch = self._reg["orchestrator"]

    def run_cycle(
        self,
        universe: List[str],
        days: int = 200,
        no_risk: bool = False,
    ) -> Dict[str, Any]:
        """Run a simple cycle.

        For now, this executes a single-symbol backtest using the first symbol in
        `universe`. This keeps the API stable while the multi-symbol live loop is
        built out in later phases.
        """

        if not universe:
            raise ValueError("universe must contain at least one symbol")

        symbol = universe[0]
        req = BacktestRequest(
            symbol=symbol,
            days=int(days),
            starting_cash=self._starting_capital,
            no_risk=bool(no_risk),
        )
        result = self._orch.run_backtest(req)

        final_portfolio = getattr(result, "final_portfolio", None)
        if final_portfolio is None:
            final_portfolio = getattr(result, "portfolio", None)

        trade_history = getattr(result, "trade_history", None)
        if trade_history is None:
            trade_history = getattr(result, "trades", None)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": self._orch.run_id,
            "mode": "BACKTEST",
            "universe": list(universe),
            "backtest": {
                "symbol": symbol,
                "days": int(days),
                "no_risk": bool(no_risk),
            },
            "trader": {
                "portfolio": final_portfolio,
                "fills": trade_history,
            },
        }
