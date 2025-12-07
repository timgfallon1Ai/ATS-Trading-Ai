from typing import Any, Dict, List

from ats.backtester2.analytics.attribution import AttributionEngine
from ats.backtester2.analytics.portfolio_analytics import PortfolioAnalytics
from ats.backtester2.analytics.trade_reconstructor import TradeReconstructor
from ats.backtester2.analytics.trade_stats import TradeStats


class AnalyticsEngine:
    """Aggregates all analytics layers and produces:
    - trade list
    - trade statistics
    - portfolio statistics
    - attribution
    """

    def __init__(self):
        self.reconstructor = TradeReconstructor()

    def on_executions(self, executions: List[Dict[str, Any]]):
        """Feed each bar’s executions into the trade reconstructor."""
        self.reconstructor.process_executions(executions)

    def finalize(self, equity_curve: List[Dict[str, Any]]) -> Dict[str, Any]:
        trades = self.reconstructor.finalize()

        return {
            "trades": trades,
            "trade_stats": TradeStats.compute(trades),
            "portfolio_stats": PortfolioAnalytics.compute(equity_curve),
            "attribution_symbol": AttributionEngine.by_symbol(trades),
            "attribution_strategy": AttributionEngine.by_strategy(trades),
        }
