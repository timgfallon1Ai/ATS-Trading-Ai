from __future__ import annotations

# ruff: noqa
"""
ATS trading system package root.

Intentionally avoids importing heavy subpackages on import, to keep
startup cheap and prevent circular-import issues.
"""

__all__: list[str] = []
