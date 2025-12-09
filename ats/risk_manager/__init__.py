"""
Risk management layer for the ATS.

Phase 3 baseline exposes a simple, numeric risk manager that can be
used by both backtests and live trading:

- RiskConfig: configuration for basic per-order limits.
- RiskDecision: result of evaluating a batch of orders.
- RiskManager: engine that applies the config to incoming orders.

The interface is intentionally small and stable so more advanced
risk modules (RM2, RM3, RM4, etc.) can be layered in later without
breaking existing call sites.
"""

from .risk_manager import RiskConfig, RiskDecision, RiskManager

__all__ = ["RiskConfig", "RiskDecision", "RiskManager"]
