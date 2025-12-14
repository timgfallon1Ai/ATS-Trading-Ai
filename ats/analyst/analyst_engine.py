from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence

import pandas as pd

from ats.analyst.feature_engine import FeatureEngine
from ats.analyst.strategy_api import FeatureRow, StrategySignal
from ats.analyst.strategy_base import StrategyBase
from ats.types import AggregatedAllocation


@dataclass
class AnalystEngine:
    """Run a collection of strategies and aggregate their output."""

    strategies: Sequence[StrategyBase]
    feature_engine: FeatureEngine = field(default_factory=FeatureEngine)

    def evaluate(
        self,
        symbol: str,
        history: pd.DataFrame,
        timestamp: pd.Timestamp,
    ) -> AggregatedAllocation:
        """Evaluate all strategies for the latest bar in `history`."""

        if history.empty:
            return AggregatedAllocation(
                symbol=symbol,
                score=0.0,
                confidence=0.0,
                timestamp=str(timestamp),
                strategy_breakdown={},
            )

        features: FeatureRow = self.feature_engine.compute(history)

        signals: List[StrategySignal] = []
        for strat in self.strategies:
            signal = strat.generate_signal(symbol, features, history).normalized()
            if signal.confidence <= 0.0:
                continue
            signals.append(signal)

        if not signals:
            return AggregatedAllocation(
                symbol=symbol,
                score=0.0,
                confidence=0.0,
                timestamp=str(timestamp),
                strategy_breakdown={},
            )

        total_conf = sum(s.confidence for s in signals)
        if total_conf <= 0.0:
            avg_score = 0.0
            avg_conf = 0.0
        else:
            avg_score = sum(s.score * s.confidence for s in signals) / total_conf
            avg_conf = total_conf / float(len(signals))

        breakdown: Dict[str, float] = {s.strategy_name: s.score for s in signals}

        allocation: AggregatedAllocation = AggregatedAllocation(
            symbol=symbol,
            score=float(max(-1.0, min(1.0, avg_score))),
            confidence=float(max(0.0, min(1.0, avg_conf))),
            timestamp=str(timestamp),
            strategy_breakdown=breakdown,
        )

        return allocation
