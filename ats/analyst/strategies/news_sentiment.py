from __future__ import annotations

import pandas as pd

from ats.analyst.strategy_api import FeatureRow, StrategySignal
from ats.analyst.strategy_base import StrategyBase


class NewsSentimentStrategy(StrategyBase):
    """Bridge to the news-sentiment subsystem.

    For now: neutral unless a `news_sentiment` feature is provided.
    """

    def generate_signal(
        self,
        symbol: str,
        features: FeatureRow,
        history: pd.DataFrame,
    ) -> StrategySignal:
        sentiment = float(features.get("news_sentiment", 0.0))

        if sentiment == 0.0:
            return StrategySignal(
                symbol=symbol,
                strategy_name=self.name,
                score=0.0,
                confidence=0.0,
                metadata={"reason": "no sentiment signal available"},
            )

        score = max(-1.0, min(1.0, sentiment))
        confidence = min(1.0, abs(sentiment))

        return StrategySignal(
            symbol=symbol,
            strategy_name=self.name,
            score=score,
            confidence=confidence,
            metadata={"sentiment": sentiment},
        )
