from __future__ import annotations

from typing import Dict


class RMInputTransform:
    """Converts PositionSizer output → RM-Master input (RMI-1 Contract).
    This ensures all RM layers receive a uniform, validated structure.
    """

    def __call__(self, sized: Dict[str, Dict]) -> Dict[str, Dict]:
        """sized[symbol] = {
            'dollar_allocation': float,
            'signal': float,
            'features': dict,
            'strategy_mix': dict
        }
        """
        result: Dict[str, Dict] = {}

        for symbol, block in sized.items():

            result[symbol] = {
                "symbol": symbol,
                "dollars": float(block["dollar_allocation"]),
                "signal": float(block["signal"]),
                "features": dict(block["features"]),
                "strategy_mix": dict(block["strategy_mix"]),
                # RM-2 will fill these in later
                "risk": {
                    "volatility": 0.0,
                    "entropy": 0.0,
                    "predictive_score": 0.0,
                },
            }

        return result
