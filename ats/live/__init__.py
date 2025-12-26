from __future__ import annotations

"""Live trading runtime (Phase 15).

This package contains a safety-gated live runner:
- Market data providers (Polygon or mock)
- Broker adapters (paper or IBKR)
- Live strategies (Phase15.1: buy_and_hold, Phase15.2: analyst_ensemble)
"""

from ats.live.config import LiveConfig
from ats.live.runner import run_live

__all__ = ["LiveConfig", "run_live"]
