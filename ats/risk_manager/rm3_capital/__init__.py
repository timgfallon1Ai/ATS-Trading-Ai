"""RM-3 Capital, Exposure, and Concentration Rules.

RM-3 translates upstream allocation intent into a constrained portfolio-level
set of target weights, respecting:

- per-symbol exposure caps
- portfolio gross/net exposure caps
- optional strategy concentration limits

Outputs are **signed weights** (positive = long, negative = short).
"""

from .capital_allocator import CapitalAllocator, CapitalAllocatorConfig  # noqa: F401
from .concentration_limits import (  # noqa: F401
    ConcentrationLimits,
    StrategyConcentrationSnapshot,
)
from .exposure_rules import ExposureRules, ExposureSnapshot  # noqa: F401

__all__ = [
    "CapitalAllocator",
    "CapitalAllocatorConfig",
    "ConcentrationLimits",
    "StrategyConcentrationSnapshot",
    "ExposureRules",
    "ExposureSnapshot",
]
