from __future__ import annotations

from typing import Any, Dict


class OrderConverter:
    """Converts:
        {symbol, final_size, side}
    Into:
        {symbol, size_delta, side, type, meta}
    """

    def convert(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        symbol = intent["symbol"]
        size = float(intent["final_size"])
        side = intent.get("side", "buy")

        size_delta = size if side == "buy" else -size

        return {
            "symbol": symbol,
            "size_delta": size_delta,
            "side": side,
            "type": "market",
            "meta": {"generated_from": "live_intent"},
        }
