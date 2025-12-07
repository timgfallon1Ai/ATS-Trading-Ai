from __future__ import annotations

from typing import Any, Dict


class PredictiveRiskEngine:
    """RM-2 Predictive Risk Engine.
    Produces contract-standard predictive overlays for each symbol.

    Input (from Hybrid Analyst):
        features[symbol] : Dict[str, float]
        predictions[symbol] : float        # model_score
        volatility[symbol] : float         # annualized or bar vol
        risk[symbol] : float               # model forecasted risk

    Output (PredictivePacket per symbol):
        {
            "symbol": str,
            "model_score": float,
            "volatility": float,
            "predicted_risk": float,
            "regime": str,                # bull / bear / neutral
            "risk_score": float            # 0.0–1.0 normalized risk
        }
    """

    # ---------------------------------------------------------
    # Normalize risk for RM-3 Allocator and RM-4 Posture engine
    # ---------------------------------------------------------
    def _normalize(self, value: float, min_v: float, max_v: float) -> float:
        if max_v == min_v:
            return 0.5
        return max(0.0, min(1.0, (value - min_v) / (max_v - min_v)))

    # ---------------------------------------------------------
    # Regime classification
    # ---------------------------------------------------------
    def _classify_regime(self, vol: float, score: float) -> str:
        """A lightweight RM-2 regime classifier:
        - High vol + negative score → BEAR
        - Low vol + positive score → BULL
        - Otherwise → NEUTRAL
        """
        if vol > 0.04 and score < 0:
            return "bear"
        if vol < 0.02 and score > 0:
            return "bull"
        return "neutral"

    # ---------------------------------------------------------
    # Main predictive risk generation
    # ---------------------------------------------------------
    def generate_predictive_packets(
        self,
        features: Dict[str, Dict[str, float]],
        predictions: Dict[str, float],
        volatility: Dict[str, float],
        predicted_risk: Dict[str, float],
    ) -> Dict[str, Dict[str, Any]]:
        """Transforms Hybrid Analyst output → RM-2 PredictivePackets.

        Returns:
            packets[symbol] : Dict with RM-contract fields.

        """
        packets: Dict[str, Dict[str, Any]] = {}

        if not predictions:
            return packets

        # Normalization anchors
        scores = list(predictions.values())
        risks = list(predicted_risk.values())

        min_score, max_score = min(scores), max(scores)
        min_risk, max_risk = min(risks), max(risks)

        for symbol, score in predictions.items():
            vol = volatility.get(symbol, 0.02)
            pr = predicted_risk.get(symbol, 0.01)

            regime = self._classify_regime(vol, score)
            risk_score = self._normalize(pr, min_risk, max_risk)

            packets[symbol] = {
                "symbol": symbol,
                "model_score": score,
                "volatility": vol,
                "predicted_risk": pr,
                "regime": regime,
                "risk_score": risk_score,
            }

        return packets
