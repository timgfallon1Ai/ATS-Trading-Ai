from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd

from ats.analyst.feature_engine import FeatureEngine
from ats.analyst.strategy_api import FeatureRow, StrategySignal
from ats.analyst.strategy_base import StrategyBase
from ats.analyst.strategies.arbitrage import ArbitrageStrategy
from ats.analyst.strategies.breakout import BreakoutStrategy
from ats.analyst.strategies.earnings import EarningsStrategy
from ats.analyst.strategies.macro_trend import MacroTrendStrategy
from ats.analyst.strategies.mean_reversion import MeanReversionStrategy
from ats.analyst.strategies.momentum import MomentumStrategy
from ats.analyst.strategies.multi_factor import MultiFactorStrategy
from ats.analyst.strategies.news_sentiment import NewsSentimentStrategy
from ats.analyst.strategies.pattern_recognition import PatternRecognitionStrategy
from ats.analyst.strategies.scalping import ScalpingStrategy
from ats.analyst.strategies.swing import SwingStrategy
from ats.analyst.strategies.volatility_regime import VolatilityRegimeStrategy
from ats.live.broker import Broker
from ats.live.strategy import LiveStrategy
from ats.live.types import Bar
from ats.trader.order import Order

log = logging.getLogger("ats.live.strategies.analyst_ensemble")


@dataclass(frozen=True)
class EnsembleDecision:
    symbol: str
    score: float
    confidence: float
    direction: int  # -1,0,1
    per_strategy: Dict[str, Dict[str, float]]


class AnalystEnsembleStrategy(LiveStrategy):
    """Runs the 12 analyst strategies each tick and converts the ensemble output into target positions."""

    name = "analyst_ensemble"

    STRATEGY_BUILDERS: List[Tuple[str, type]] = [
        ("momentum", MomentumStrategy),
        ("mean_reversion", MeanReversionStrategy),
        ("breakout", BreakoutStrategy),
        ("scalping", ScalpingStrategy),
        ("arbitrage", ArbitrageStrategy),
        ("swing", SwingStrategy),
        ("earnings", EarningsStrategy),
        ("macro_trend", MacroTrendStrategy),
        ("news_sentiment", NewsSentimentStrategy),
        ("volatility_regime", VolatilityRegimeStrategy),
        ("pattern_recognition", PatternRecognitionStrategy),
        ("multi_factor", MultiFactorStrategy),
    ]

    def __init__(
        self,
        notional_per_symbol: float,
        allow_fractional: bool,
        history_bars: int,
        warmup_bars: int,
        min_confidence: float,
        allow_short: bool,
        rebalance_threshold_notional: float,
        log_signals: bool,
    ) -> None:
        self.notional_per_symbol = float(notional_per_symbol)
        self.allow_fractional = bool(allow_fractional)
        self.history_bars = int(history_bars)
        self.warmup_bars = int(warmup_bars)
        self.min_confidence = float(min_confidence)
        self.allow_short = bool(allow_short)
        self.rebalance_threshold_notional = float(rebalance_threshold_notional)
        self.log_signals = bool(log_signals)

        self._feature_engine = FeatureEngine()
        self._strategies: List[StrategyBase] = [
            cls() for _, cls in self.STRATEGY_BUILDERS
        ]
        self._history: Dict[str, pd.DataFrame] = {}

        log.info(
            "AnalystEnsembleStrategy loaded %d strategies: %s",
            len(self._strategies),
            ", ".join([s.name for s in self._strategies]),
        )

    def _append_bar(self, sym: str, bar: Bar) -> pd.DataFrame:
        df = self._history.get(sym)
        row = {
            "open": float(bar.open),
            "high": float(bar.high),
            "low": float(bar.low),
            "close": float(bar.close),
            "volume": float(bar.volume),
        }
        idx = pd.to_datetime([bar.timestamp])

        if df is None or df.empty:
            df = pd.DataFrame([row], index=idx)
        else:
            new = pd.DataFrame([row], index=idx)
            df = pd.concat([df, new], axis=0)

        # Drop duplicate timestamps; keep last
        df = df[~df.index.duplicated(keep="last")]

        # Keep rolling window
        if len(df) > self.history_bars:
            df = df.iloc[-self.history_bars :]

        self._history[sym] = df
        return df

    def _ensemble(self, sym: str, history: pd.DataFrame) -> EnsembleDecision:
        features: FeatureRow = self._feature_engine.compute(history)

        signals: List[StrategySignal] = []
        for strat in self._strategies:
            try:
                sig = strat.generate_signal(sym, features, history)
            except Exception as e:
                log.exception("Strategy %s crashed for %s: %s", strat.name, sym, e)
                sig = StrategySignal(
                    symbol=sym,
                    strategy_name=strat.name,
                    score=0.0,
                    confidence=0.0,
                    metadata={"error": "exception"},
                )
            signals.append(sig)

        total_w = sum(max(0.0, float(s.confidence)) for s in signals)
        if total_w <= 1e-12:
            score = 0.0
        else:
            score = (
                sum(float(s.score) * max(0.0, float(s.confidence)) for s in signals)
                / total_w
            )

        # Convert ensemble score to direction and confidence.
        direction = 0
        if score > 0.05:
            direction = 1
        elif score < -0.05:
            direction = -1

        confidence = min(1.0, abs(score))

        per: Dict[str, Dict[str, float]] = {
            s.strategy_name: {
                "score": float(s.score),
                "confidence": float(s.confidence),
            }
            for s in signals
        }

        return EnsembleDecision(
            symbol=sym,
            score=float(score),
            confidence=float(confidence),
            direction=int(direction),
            per_strategy=per,
        )

    def _target_qty(
        self, bar: Bar, decision: EnsembleDecision, current_qty: float
    ) -> float:
        px = float(bar.close)
        if px <= 0:
            return 0.0

        if decision.confidence < self.min_confidence:
            # Low confidence => hold (no change)
            return float(current_qty)

        notional = self.notional_per_symbol * decision.confidence

        if decision.direction == 1:
            target = notional / px
        elif decision.direction == -1:
            if not self.allow_short:
                # If we don't short, interpret -1 as "flat"
                target = 0.0
            else:
                target = -(notional / px)
        else:
            target = 0.0

        if not self.allow_fractional:
            # Truncate toward 0
            if target > 0:
                target = float(int(target))
            else:
                target = -float(int(abs(target)))

        return float(target)

    def on_tick(self, bars: Dict[str, Bar], broker: Broker) -> List[Order]:
        orders: List[Order] = []
        positions = broker.get_positions()

        for sym, bar in bars.items():
            sym = sym.upper()
            hist = self._append_bar(sym, bar)

            if len(hist) < self.warmup_bars:
                continue

            decision = self._ensemble(sym, hist)
            if self.log_signals:
                log.info(
                    "ENSEMBLE %s dir=%s score=%.4f conf=%.3f",
                    sym,
                    decision.direction,
                    decision.score,
                    decision.confidence,
                )

            current_qty = float(positions.get(sym, 0.0))
            target_qty = self._target_qty(bar, decision, current_qty)

            delta_qty = float(target_qty - current_qty)
            delta_notional = abs(delta_qty) * float(bar.close)

            if delta_notional < self.rebalance_threshold_notional:
                continue

            if delta_qty > 0:
                orders.append(
                    Order(
                        symbol=sym, side="buy", size=abs(delta_qty), order_type="market"
                    )
                )
            else:
                orders.append(
                    Order(
                        symbol=sym,
                        side="sell",
                        size=abs(delta_qty),
                        order_type="market",
                    )
                )

        return orders
