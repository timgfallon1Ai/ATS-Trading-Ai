# ats/risk_manager/risk_dispatcher.py

from __future__ import annotations

from typing import Any, Dict

from .rm4_posture.rm4_agent import RM4Agent
from .rm4_posture.rm4_state_machine import RM4StateMachine


class RiskDispatcher:
    """Dispatcher wrapper around RM-4 Posture Engine.

    BT-2A Contract:
    ----------------
    run_risk(ts, signals, portfolio) ->
        { symbol: adjusted_signal }

    Notes:
    - `signals` is { symbol: raw_signal }
    - `portfolio` is any pipeline-friendly dict provided by the backtester

    """

    def __init__(self):
        # RM-4 uses a state machine + a controller agent
        self.state_machine = RM4StateMachine()
        self.agent = RM4Agent(self.state_machine)

    # ------------------------------------------------------------------
    # Posture computation
    # ------------------------------------------------------------------
    def run_risk(
        self, ts: int, signals: Dict[str, float], portfolio: Dict[str, Any]
    ) -> Dict[str, float]:
        """Returns:
            { symbol: risk_adjusted_signal }

        Steps:
        1) Update RM-4 state from portfolio
        2) Compute posture (risk multiplier)
        3) Multiply raw signals by posture factor

        """
        # Update posture state (RM-4 is fully self-contained)
        posture = self.agent.compute_posture(
            timestamp=ts, portfolio=portfolio, signals=signals
        )

        # posture is a float in [0, 1]
        multiplier = posture.get("multiplier", 1.0)

        out = {}
        for sym, sig in signals.items():
            out[sym] = sig * multiplier

        return out
