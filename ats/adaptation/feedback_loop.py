from .meta_allocator import MetaAllocator
from .regime_adapter import RegimeAdapter
from .reputation_engine import ReputationEngine


class AdaptationController:
    """Full feedback loop:

    ReputationEngine → MetaAllocator → RegimeAdapter → output weights
    """

    def __init__(self):
        self.reputation = ReputationEngine()
        self.meta = MetaAllocator()
        self.regime = RegimeAdapter()

    def update(
        self, rm_orders, exec_report, vol_estimate: float, governance_events: int
    ):
        # Extract strategy breakdown
        if rm_orders:
            breakdown = rm_orders[0].get("strategy_breakdown", {})
        else:
            breakdown = {}

        pnl = (
            exec_report["portfolio_value"] - exec_report["portfolio_value"]
        )  # optional per-bar

        # Update reputation
        self.reputation.update(
            strategy_breakdown=breakdown, pnl=pnl, governance_events=governance_events
        )

        # Convert to meta-weights
        weights = self.meta.compute_weights(self.reputation.get_scores())

        # Adjust weights for regime
        regime = self.regime.classify(vol_estimate)
        adjusted_weights = self.regime.adjust(weights, regime)

        return {
            "weights": adjusted_weights,
            "reputation": self.reputation.get_scores(),
            "regime": regime,
        }
