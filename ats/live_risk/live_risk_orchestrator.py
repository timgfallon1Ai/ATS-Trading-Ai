from __future__ import annotations

from typing import Any, Dict, List

from .live_risk_adapter import LiveRiskAdapter
from .live_risk_envelope import LiveRiskEnvelope


class LiveRiskOrchestrator:
    """Receives strategy signals → applies risk envelope → forwards
    risk-filtered signals to the live aggregator.
    """

    def __init__(self, adapter: LiveRiskAdapter) -> None:
        self.adapter = adapter

    def process(
        self, merged: Dict[str, Any], signals: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        envelope: LiveRiskEnvelope = self.adapter.evaluate(merged)
        out: List[Dict[str, Any]] = []

        for sig in signals:
            size = float(sig.get("size", 1.0))

            if size * merged["price"]["close"] > envelope.max_capital_risk:
                continue  # risk budget exceeded

            if envelope.require_confirmation:
                if not sig.get("confirmed", False):
                    continue

            sig_out = sig.copy()
            sig_out["risk"] = envelope.to_dict()
            out.append(sig_out)

        return out
