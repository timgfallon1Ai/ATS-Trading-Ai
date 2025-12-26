"""Live trading components (Phase 15).

This package intentionally keeps a small, testable surface area:
- Market data providers (polling-based in Phase 15.1)
- Broker adapters (paper by default; IBKR optional)
- Simple strategies and a runner loop

NOTE: Nothing in here is financial advice. Use paper trading first.
"""

from .config import LiveConfig
from .runner import LiveRunner
from .types import OrderFill, OrderRequest, PriceTick

__all__ = [
    "LiveConfig",
    "LiveRunner",
    "OrderFill",
    "OrderRequest",
    "PriceTick",
]
