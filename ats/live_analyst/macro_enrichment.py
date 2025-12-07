from __future__ import annotations

from typing import Any, Dict, Optional


class MacroEnrichment:
    """Lightweight placeholder with deterministic scoring.

    Could be upgraded later to:
    - economic calendar
    - yield curve
    - rates volatility
    - VIX regime
    """

    def score(self, symbol: str, merged: Dict[str, Any]) -> Optional[float]:
        # Deterministic stable value for now
        return 0.15
