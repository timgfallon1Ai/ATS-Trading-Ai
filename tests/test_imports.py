from __future__ import annotations

import importlib


def test_core_imports_smoke() -> None:
    """
    Fast import smoke test to catch circular imports / missing modules.
    Keep this list focused on "always required" runtime modules.
    """
    modules = [
        "ats",
        "ats.types",
        "ats.core",
        "ats.core.clock",
        "ats.analyst",
        "ats.aggregator",
        "ats.risk_manager.risk_manager",
        "ats.trader.trader",
        "ats.backtester2.engine",
        "ats.backtester2.run",
        "ats.run",  # package import (python -m ats.run uses __main__.py)
    ]

    failures: list[str] = []
    for mod in modules:
        try:
            importlib.import_module(mod)
        except Exception as e:  # noqa: BLE001
            failures.append(f"{mod}: {type(e).__name__}: {e}")

    assert not failures, "Import failures:\n" + "\n".join(failures)
