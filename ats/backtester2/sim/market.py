# ats/backtester2/sim/market.py

from __future__ import annotations

from typing import List

from ats.backtester2.core.bar import Bar
from ats.backtester2.core.timeline import Timeline

from .execution import ExecutionEngine
from .fills import Fill
from .orders import Order


class SimulationMarket:
    """Provides the bridge between:
    - BacktestEngine
    - ExecutionEngine
    - Historical timeline
    """

    def __init__(self, timeline: Timeline, execution: ExecutionEngine):
        self.timeline = timeline
        self.execution = execution
        self.current_bar: Bar | None = None

    # ------------------------------
    # MARKET ADVANCE
    # ------------------------------
    def step(self) -> List[Fill] | None:
        bar = self.timeline.next_bar()
        if bar is None:
            return None

        self.current_bar = bar
        fills = self.execution.process(bar)
        return fills

    # ------------------------------
    # ORDER INTAKE
    # ------------------------------
    def submit(self, order: Order) -> None:
        self.execution.submit(order)

    def at_end(self) -> bool:
        return self.timeline.at_end()
