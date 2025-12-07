from __future__ import annotations

from typing import Any, Dict


class PositionSizer:
    """Converts per-symbol raw signals → normalized strength values.

    Rules (S2 + U1 + Z-Ultra compliant):
        - strength = abs(signal)
        - normalized to [0,1]
        - ensures RM-MASTER sees clean scalar intensity
    """

    def size(
        self,
        analyst_output: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        signals = {sym: abs(v["signal"]) for sym, v in analyst_output.items()}
        max_sig = max(signals.values()) if signals else 1.0

        result: Dict[str, Dict[str, Any]] = {}

        for symbol, payload in analyst_output.items():
            raw = payload["signal"]
            strength = abs(raw) / max_sig if max_sig > 0 else 0.0

            result[symbol] = {
                **payload,
                "signal": raw,
                "strength": strength,
            }

        return result
