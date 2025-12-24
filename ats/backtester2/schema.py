from __future__ import annotations

"""
ats.backtester2.schema

Compatibility shim.

Some earlier modules referenced `ats.backtester2.schema` for Bar/Order.
Backtester2 now defines Bar in `ats.backtester2.types` and Order in
`ats.trader.order_types`.

This module exists purely to avoid ModuleNotFoundError in older imports.
"""

from ats.trader.order_types import Order
from .types import Bar

__all__ = ["Bar", "Order"]
