from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

# Types
from ats.types import (
    AggregatedAllocation,
    RiskBatchOutput,
    RiskPacket,
)

from .rm1_baseline.baseline_rules import BaselineRules

# RM-1
from .rm1_baseline.sanity_checks import SanityChecks
from .rm2_predictive.predictive_engine import PredictiveEngine

# RM-2
from .rm2_predictive.regime_classifier import RegimeClassifier
from .rm3_capital.capital_allocator import CapitalAllocator
from .rm3_capital.concentration_limits import ConcentrationLimits

# RM-3
from .rm3_capital.exposure_rules import ExposureRules
from .rm4_posture.rm4_agent import RM4Agent

# RM-4
from .rm4_posture.rm4_state_machine import RM4StateMachine
from .rm5_execution_filters.fills_model import FillsModel
from .rm5_execution_filters.latency_model import LatencyModel

# RM-5
from .rm5_execution_filters.slippage_model import SlippageModel
from .rm6_portfolio_health.portfolio_scoring import PortfolioScoring

# RM-6
from .rm6_portfolio_health.portfolio_state import PortfolioState

# RM-7
from .rm7_governance.governance_bus import GovernanceBus
from .rm7_governance.governance_state import GovernanceState

# ======================================================================
#                           MASTER RISK MANAGER
# ======================================================================


class RiskManager:
    """Unified institutional RM-MASTER pipeline (RM-1 → RM-7).

    Executes, for each symbol:
        • Baseline screening
        • Predictive risk scoring
        • Capital allocation
        • Posture state transitions
        • Execution slippage/latency/fill modeling
        • Portfolio health updates
        • Governance event logging

    Produces:
        RiskPacket  — per symbol
        RiskBatchOutput — dictionary of all packets
    """

    # --------------------------------------------------------------
    # Utilities
    # --------------------------------------------------------------
    def _ts(self) -> str:
        return datetime.utcnow().isoformat()

    # --------------------------------------------------------------
    # Constructor
    # --------------------------------------------------------------
    def __init__(self, base_capital: float = 1000.0):
        # RM-1
        self.sanity = SanityChecks()
        self.baseline = BaselineRules()

        # RM-2
        self.regimes = RegimeClassifier()
        self.predictor = PredictiveEngine()

        # RM-3
        self.exposure = ExposureRules()
        self.concentration = ConcentrationLimits()
        self.capital = CapitalAllocator(
            base_capital=base_capital,
            exposure=self.exposure,
            concentration=self.concentration,
        )

        # RM-4
        self.state_machine = RM4StateMachine()
        self.rm4_agent = RM4Agent()

        # RM-5
        self.slip_model = SlippageModel()
        self.latency_model = LatencyModel()
        self.fill_model = FillsModel()

        # RM-6
        self.portfolio_state = PortfolioState()
        self.portfolio_score = PortfolioScoring()

        # RM-7
        self.gov_bus = GovernanceBus()
        self.gov_state = GovernanceState()

    # =====================================================================
    # INTERNAL: Process a single symbol
    # =====================================================================
    def _process_symbol(
        self,
        symbol: str,
        alloc: AggregatedAllocation,
        features: Dict[str, Any],
        strategy_meta: Dict[str, Any],
    ) -> RiskPacket:
        """Executes RM-1 → RM-7 for a single symbol."""
        # -------------------------
        # RM-1: Baseline
        # -------------------------
        rm1_pass, rm1_notes = self.sanity.check(symbol, alloc)
        baseline_adj = self.baseline.adjust(alloc)

        # -------------------------
        # RM-2: Predictive
        # -------------------------
        regime = self.regimes.classify(features)
        pred = self.predictor.predict(
            symbol=symbol,
            features=features,
            strategy_meta=strategy_meta,
            regime=regime,
        )

        # -------------------------
        # RM-3: Capital Allocation
        # -------------------------
        capital_out = self.capital.allocate_symbol(
            symbol=symbol,
            alloc=baseline_adj,
            predictive=pred,
        )

        # -------------------------
        # RM-4: Posture
        # -------------------------
        posture, posture_notes = self.state_machine.transition(
            symbol=symbol,
            anomaly=pred.get("anomaly_score", 0.0),
            drift=pred.get("drift_score", 0.0),
            predictive_risk=pred.get("risk_score", 0.0),
        )

        adj_capital = self.rm4_agent.adjust(
            symbol=symbol,
            capital=capital_out,
            posture=posture,
            predictive=pred,
        )

        # -------------------------
        # RM-5: Execution Filters
        # -------------------------
        slippage = self.slip_model.compute_slippage(
            volatility=features.get("volatility", 0.02),
            size=adj_capital["final_capital"],
            entropy=features.get("entropy", 0.1),
        )

        latency_val = self.latency_model.compute_latency(features)

        fill = self.fill_model.compute_fill(
            alloc=adj_capital,
            slippage=slippage,
            latency=latency_val,
        )

        # -------------------------
        # RM-6: Portfolio Health
        # -------------------------
        portfolio_health = self.portfolio_score.score(
            state=self.portfolio_state,
            pnl=pred.get("pnl_estimate", 0.0),
            alloc=adj_capital,
        )

        # -------------------------
        # RM-7: Governance
        # -------------------------
        self.gov_bus.push_event(
            symbol=symbol,
            stage="RM",
            message="RM-complete",
            details={
                "posture": posture,
                "rm1_notes": rm1_notes,
                "posture_notes": posture_notes,
            },
        )

        self.gov_state.record_event(
            symbol=symbol,
            posture=posture,
            risk_score=pred.get("risk_score", 0.0),
            timestamp=self._ts(),
        )

        # -------------------------
        # Assemble RiskPacket
        # -------------------------
        packet: RiskPacket = {
            "symbol": symbol,
            "rm1": {
                "pass": rm1_pass,
                "notes": rm1_notes,
            },
            "predictive": pred,
            "capital": adj_capital,
            "execution": {
                "slippage": slippage,
                "latency": latency_val,
                "fill": fill,
            },
            "portfolio": portfolio_health,
            "posture": posture,
            "timestamp": self._ts(),
        }

        return packet

    # =====================================================================
    # PUBLIC: Batch Processing
    # =====================================================================
    def run_batch(
        self,
        allocations: Dict[str, AggregatedAllocation],
        features: Dict[str, Dict[str, Any]],
        strategy_meta: Dict[str, Dict[str, Any]],
    ) -> RiskBatchOutput:
        """Runs RM-MASTER on all symbols in a batch."""
        out: RiskBatchOutput = {"packets": {}}

        for symbol, alloc in allocations.items():
            pkt = self._process_symbol(
                symbol=symbol,
                alloc=alloc,
                features=features.get(symbol, {}),
                strategy_meta=strategy_meta.get(symbol, {}),
            )
            out["packets"][symbol] = pkt

        return out
