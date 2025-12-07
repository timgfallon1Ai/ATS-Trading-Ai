# ats/analyst/strategy_manager.py
from __future__ import annotations

from typing import Dict

from ats.types import FeatureMap

from .strategies.arbitrage import ArbitrageStrategy
from .strategies.breakout import BreakoutStrategy

# Import all 12 strategies
from .strategies.earnings import EarningsStrategy
from .strategies.macro_trend import MacroTrendStrategy
from .strategies.mean_reversion import MeanReversionStrategy
from .strategies.momentum import MomentumStrategy
from .strategies.multi_factor import MultiFactorStrategy
from .strategies.news_sentiment import NewsSentimentStrategy
from .strategies.scalping import ScalpingStrategy
from .strategies.swing import SwingStrategy
from .strategies.value import ValueStrategy  # If missing, I will generate next.
from .strategies.volatility_regime import VolatilityRegimeStrategy


class StrategyManager:
    """Runs all 12 strategies and standardizes output for AnalystEngine.

    Output format (MM-2):
        {
            "features": Dict[str, FeatureMap],
            "raw_signals": Dict[str, Dict[str, float]],
            "pnl_estimates": Dict[str, float],
            "risk_vol": Dict[str, float],
        }
    """

    def __init__(self):
        self.strategies = {
            "earnings": EarningsStrategy(),
            "mean_reversion": MeanReversionStrategy(),
            "arbitrage": ArbitrageStrategy(),
            "breakout": BreakoutStrategy(),
            "macro_trend": MacroTrendStrategy(),
            "momentum": MomentumStrategy(),
            "multi_factor": MultiFactorStrategy(),
            "news_sentiment": NewsSentimentStrategy(),
            "scalping": ScalpingStrategy(),
            "swing": SwingStrategy(),
            "volatility_regime": VolatilityRegimeStrategy(),
            "value": ValueStrategy(),
        }

    # ----------------------------------------------------------------------
    # CORE RUNNER
    # ----------------------------------------------------------------------
    def run_all(self, market: Dict) -> Dict:
        """Runs all 12 alpha models and aggregates:

        Features (per symbol)
        Strategy signals (per strategy)
        PnL estimates (per strategy)
        Volatility estimates (per strategy)
        """
        features_out: Dict[str, FeatureMap] = {}
        signals_out: Dict[str, Dict[str, float]] = {}
        pnl_out: Dict[str, float] = {}
        vol_out: Dict[str, float] = {}

        # -----------------------------------
        # 1) Run each strategy
        # -----------------------------------
        for strat_name, strat in self.strategies.items():
            result = strat.run(market)

            # Expected result shape from each strategy:
            # {
            #   "features": Dict[str, FeatureMap],
            #   "signal": Dict[str, float],
            #   "pnl_estimate": float,
            #   "vol_estimate": float,
            # }

            strat_features = result.get("features", {})
            strat_signal = result.get("signal", {})
            strat_pnl = result.get("pnl_estimate", 0.0)
            strat_vol = result.get("vol_estimate", 1.0)

            # -----------------------------------
            # Collect features (symbol-by-symbol)
            # -----------------------------------
            for symbol, fmap in strat_features.items():
                if symbol not in features_out:
                    features_out[symbol] = fmap
                else:
                    # Merge inline, later strategies override duplicate keys
                    features_out[symbol].update(fmap)

            # -----------------------------------
            # Collect raw signals
            # -----------------------------------
            signals_out[strat_name] = strat_signal

            # -----------------------------------
            # Collect PNL / VOL estimates
            # -----------------------------------
            pnl_out[strat_name] = float(strat_pnl)
            vol_out[strat_name] = max(
                0.0001, float(strat_vol)
            )  # Prevent divide-by-zero

        # -----------------------------------
        # Final MM-2 Packet
        # -----------------------------------
        return {
            "features": features_out,
            "raw_signals": signals_out,
            "pnl_estimates": pnl_out,
            "risk_vol": vol_out,
        }
