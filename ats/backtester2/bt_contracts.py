# ats/backtester2/bt_contracts.py

from __future__ import annotations

from typing import Any, Dict


class BT2DispatcherContract:
    """Defines the required interface for BT-2A dispatcher.
    Analysts, risk manager, sizing must implement these methods.
    """

    def run_features(
        self, ts: int, bars: Dict[str, Dict[str, float]]
    ) -> Dict[str, Any]:
        raise NotImplementedError

    def run_signals(self, ts: int, features: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def run_risk(self, ts: int, signals: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def size_positions(self, ts: int, posture: Dict[str, float]) -> Dict[str, float]:
        raise NotImplementedError
