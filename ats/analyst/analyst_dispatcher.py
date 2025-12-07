# ats/analyst/analyst_dispatcher.py

from __future__ import annotations

from typing import Dict

from .feature_engine import FeatureEngine
from .strategy_manager import StrategyManager


class AnalystDispatcher:
    """Unified interface exposing:
      - Feature extraction
      - Strategy signal generation

    Fully compatible with BT-2A dispatcher requirements.
    """

    def __init__(self):
        self.features = FeatureEngine()
        self.strategies = StrategyManager()

    # ----------------------------------------------------
    # Features
    # ----------------------------------------------------
    def run_features(
        self, ts: int, symbol_bars: Dict[str, Dict[str, float]]
    ) -> Dict[str, Dict[str, float]]:
        """Returns:
        { symbol: { feature_name: value } }

        """
        out = {}
        for sym, bar in symbol_bars.items():
            out[sym] = self.features.extract_features(ts, sym, bar)
        return out

    # ----------------------------------------------------
    # Signals
    # ----------------------------------------------------
    def run_signals(
        self, ts: int, features: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """Returns:
            { symbol: signal_strength }

        signal_strength is expected to be between -1.0 and +1.0.

        """
        out: Dict[str, float] = {}
        for sym, feats in features.items():
            out[sym] = self.strategies.generate_signal(ts, sym, feats)
        return out
