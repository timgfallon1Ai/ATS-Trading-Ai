import json
from pathlib import Path
from typing import Any, Dict


class ResultsWriter:
    """Writes backtest artifacts in a clean, structured manner.

    Output layout:

    results/
        run_config.json
        metadata.json
        trades.jsonl
        equity_curve.jsonl
        metrics.json

    This is the ONLY writer used by Backtester2.
    """

    def __init__(self, root: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

        self.trades_path = self.root / "trades.jsonl"
        self.equity_path = self.root / "equity_curve.jsonl"
        self.run_config_path = self.root / "run_config.json"
        self.metadata_path = self.root / "metadata.json"
        self.metrics_path = self.root / "metrics.json"

    # ---------------------------
    # JSON helpers
    # ---------------------------

    @staticmethod
    def _write_json(path: Path, payload: Dict[str, Any]) -> None:
        with open(path, "w") as f:
            json.dump(payload, f, indent=2)

    @staticmethod
    def _append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
        with open(path, "a") as f:
            f.write(json.dumps(payload) + "\n")

    # ---------------------------
    # Public API
    # ---------------------------

    def write_run_config(self, cfg: Dict[str, Any]) -> None:
        """Write static run configuration."""
        self._write_json(self.run_config_path, cfg)

    def write_metadata(self, meta: Dict[str, Any]) -> None:
        """Write static metadata (symbol list, bar count, timestamps)."""
        self._write_json(self.metadata_path, meta)

    def append_trade(self, trade: Dict[str, Any]) -> None:
        """Append a trade to trades.jsonl.
        Expected structure:
        {
            "timestamp": int,
            "symbol": "AAPL",
            "side": "long"|"short"|"flat",
            "qty": float,
            "entry_price": float,
            "exit_price": float,
            "pnl": float,
            ...
        }
        """
        self._append_jsonl(self.trades_path, trade)

    def append_equity_point(self, eq: Dict[str, Any]) -> None:
        """Append equity curve point:
        {
            "timestamp": int,
            "equity": float,
            "cash": float,
            "positions": {...}
        }
        """
        self._append_jsonl(self.equity_path, eq)

    def write_metrics(self, metrics: Dict[str, Any]) -> None:
        """Write final metrics such as:
        - total_return
        - sharpe
        - sortino
        - max_drawdown
        - win_rate
        - avg_win
        - avg_loss
        """
        self._write_json(self.metrics_path, metrics)
