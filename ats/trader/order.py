"""Compatibility shim for legacy imports.

Some parts of the codebase (and older scripts) import Order from `ats.trader.order`.
The canonical definition lives in `ats.trader.order_types`.

Keeping this module avoids circular imports and unblocks older import paths.
"""

from __future__ import annotations

from ats.trader.order_types import Order

__all__ = ["Order"]
