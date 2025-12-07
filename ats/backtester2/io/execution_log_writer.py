import json
from pathlib import Path
from typing import Any, Dict


class ExecutionLogWriter:
    """Streams raw execution events into execution_log.jsonl.

    This log is intended for:
        - Debugging the Trader execution simulator
        - Dashboard 'executions.html'
        - Trade reconstruction validation
        - Post-trade analytics

    Each record is a single execution fill:
    {
        "timestamp": int,
        "symbol": "AAPL",
        "side": "buy"|"sell",
        "qty": float,
        "price": float,
        "slippage": float,
        "latency_ms": float,
        "order_id": str
    }
    """

    def __init__(self, root: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "execution_log.jsonl"

    def append(self, execution: Dict[str, Any]) -> None:
        with open(self.path, "a") as f:
            f.write(json.dumps(execution) + "\n")
