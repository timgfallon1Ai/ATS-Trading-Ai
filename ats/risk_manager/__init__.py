"""ATS Institutional Risk Manager (RM-1 → RM-7)

Provides a fully modular, multi-layer risk engine:
- Baseline safety checks
- Predictive risk & regimes
- Capital exposure rules
- Posture & anomaly detection (RM-4)
- Execution filters
- Portfolio health scoring
- Governance & audit logging
"""

from .risk_manager import RiskManager
