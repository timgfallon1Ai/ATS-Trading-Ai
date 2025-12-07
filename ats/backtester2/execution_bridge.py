# ats/backtester2/execution_bridge.py

from __future__ import annotations

from typing import Any, Dict, List

from ats.backtester2.execution_engine import ExecutionEngine


class ExecutionBridge:
    """Bridges Backtester <-> ExecutionEngine.

    Calls .execute() on the ExecutionEngine and normalizes output.
    """

    def __init__(self, engine: ExecutionEngine):
        self.engine = engine

    def execute(
        self,
        instructions: List[Dict[str, Any]],
        current_bar: Dict[str, Any],
        next_bar: Dict[str, Any] | None,
        timestamp: int,
    ) -> List[Dict[str, Any]]:
        if not instructions:
            return []

        return self.engine.execute(
            instructions=instructions,
            current_bar=current_bar,
            next_bar=next_bar,
            timestamp=timestamp,
        )
