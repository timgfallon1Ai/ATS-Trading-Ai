from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import pandas as pd

from ats.analyst.strategy_api import FeatureRow, StrategySignal


class StrategyBase(ABC):
    """Base class for all analyst strategies.

    Strategies are stateless objects: they look at the current feature row
    and history window and emit a directional signal.
    """

    def __init__(self, name: Optional[str] = None) -> None:
        self.name = name or self.__class__.__name__

    @abstractmethod
    def generate_signal(
        self,
        symbol: str,
        features: FeatureRow,
        history: pd.DataFrame,
    ) -> StrategySignal:
        """Produce a signal for the latest bar in `history`."""
        raise NotImplementedError
