from __future__ import annotations

"""
ats.backtester2

Backtest v2 package.

For now, we expose only the simple runner used by `python -m ats.backtester2.run`.
The richer engine / interfaces are considered internal and may evolve.
"""

from .run import main, run_backtest

__all__ = ["main", "run_backtest"]
