"""ats.run

Unified runtime entrypoint.

Keep __init__ intentionally light to avoid circular import issues.
"""

from ats.run.boot import BootConfig, boot_system

__all__ = [
    "BootConfig",
    "boot_system",
]
