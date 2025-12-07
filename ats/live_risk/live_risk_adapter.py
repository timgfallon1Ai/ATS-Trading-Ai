from __future__ import annotations

from typing import Any, Dict

from .live_risk_envelope import LiveRiskEnvelope
from .posture_sync import PostureSync
from .volatility_guard import VolatilityGuard


class LiveRiskAdapter:
    """Applies RM1–RM7 logic in a compressed live form.

    Produces a LiveRiskEnvelope governing:
    - max allowed position
    - max capital at risk
    - posture: normal/cautious/aggressive
    - confirmation requirements
    """

    def __init__(
        self,
        volatility: VolatilityGuard,
        posture: PostureSync,
        base_risk_fraction: float = 0.02,
    ) -> None:
        self.vol = volatility
        self.posture = posture
        self.base_risk_fraction = base_risk_fraction

    # ----------------------------------------------------
    # RM1–RM7 combined into a single real-time envelope
    # ----------------------------------------------------
    def evaluate(self, merged: Dict[str, Any]) -> LiveRiskEnvelope:
        posture = self.posture.posture()

        # Base risk budget
        max_capital = self.posture.equity * self.base_risk_fraction

        # Aggression adjustments
        if posture == "aggressive":
            max_capital *= 3.0
        elif posture == "cautious":
            max_capital *= 0.5

        # Volatility tightening (RM5 style)
        require_confirmation = False
        if self.vol.spike_detected(merged):
            require_confirmation = True
            max_capital *= 0.5

        # Max position size is simply capital ÷ price
        price_close = merged["price"]["close"]
        max_position = max_capital / price_close

        return LiveRiskEnvelope(
            max_position=max_position,
            max_capital_risk=max_capital,
            require_confirmation=require_confirmation,
            posture=posture,
        )
