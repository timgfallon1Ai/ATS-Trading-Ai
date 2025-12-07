"""Dynamic Strategy Loader (Option A Architecture)

This loader imports strategy modules from ats/analyst/strategies
and ensures they are registered with the global StrategyRegistry.

It provides:
- Zero circular imports
- Guaranteed clean module loading
- Auto-registration of strategies using @register_strategy
- Clear diagnostics if a strategy fails to load
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from typing import List, Optional

from .registry import strategy_registry


# =====================================================================
# Module Discovery Utilities
# =====================================================================
def _discover_strategy_modules() -> List[str]:
    """Discover all modules inside ats/analyst/strategies.
    Returns a list of Python module names (strings) without loading them.
    """
    strategies_path = Path(__file__).parent / "strategies"

    modules = []
    for module_info in pkgutil.iter_modules([str(strategies_path)]):
        name = module_info.name
        if not name.startswith("_"):
            modules.append(name)

    return modules


# =====================================================================
# Loader
# =====================================================================
def load_all_strategies(verbose: bool = False) -> None:
    """Dynamically imports all strategy modules.

    Modules must:
        - live inside ats/analyst/strategies
        - contain classes decorated with @register_strategy
        - subclass Strategy

    After import, classes will be available via strategy_registry.
    """
    base_pkg = "ats.analyst.strategies"

    modules = _discover_strategy_modules()

    if verbose:
        print("Discovered strategy modules:", modules)

    for module_name in modules:
        fq_name = f"{base_pkg}.{module_name}"

        try:
            importlib.import_module(fq_name)
            if verbose:
                print(f"Loaded strategy module: {fq_name}")

        except Exception as exc:
            raise ImportError(
                f"Failed to load strategy module '{fq_name}': {exc}"
            ) from exc


# =====================================================================
# Optional utility
# =====================================================================
def validate_registry(min_expected: Optional[int] = None) -> None:
    """Runtime validator to ensure strategies are properly loaded.
    Useful in backtests or boot startup.
    """
    registered = strategy_registry.list_strategies()

    if min_expected is not None and len(registered) < min_expected:
        raise RuntimeError(
            f"Expected at least {min_expected} strategies, "
            f"but only {len(registered)} were loaded: {registered}"
        )


# =====================================================================
# Default runtime auto-load hook
# =====================================================================
def initialize_analyst(verbose: bool = False) -> None:
    """Primary entry point used by:
        - AnalystEngine
        - Backtester2
        - Live Trader (via orchestrator)

    Ensures all strategies are discovered, imported, and registered.
    """
    load_all_strategies(verbose=verbose)

    if verbose:
        print("Strategies registered:", strategy_registry.list_strategies())
