# ats/backtester2/signal_router.py

from __future__ import annotations

from typing import Any, Dict, List

from ats.backtester2.position_intent import PositionIntent


class SignalRouter:
    """Converts raw analyst hybrid signals -> per-symbol PositionIntent objects."""

    def __init__(self):
        pass

    def route(
        self,
        multi_symbol_signals: Dict[str, List[Dict[str, Any]]],
    ) -> List[PositionIntent]:
        """Input format:
            {
                "AAPL": [
                    {"strategy": "momentum", "score": 0.65},
                    {"strategy": "mean_rev", "score": -0.20},
                ],
                "TSLA": [
                    {"strategy": "breakout", "score": 0.90},
                ]
            }

        Output:
            List[PositionIntent]
        """
        intents: List[PositionIntent] = []

        for sym, sig_list in multi_symbol_signals.items():
            if not sig_list:
                continue

            # Aggregate strategy scores into a single blended score
            total = 0.0
            for s in sig_list:
                total += float(s["score"])

            blended = total / len(sig_list)

            intents.append(
                PositionIntent(
                    symbol=sym,
                    strength=blended,
                    raw_signals=sig_list,
                )
            )

        return intents
