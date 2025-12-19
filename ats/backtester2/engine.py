from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

from ats.risk_manager import RiskDecision, RiskManager
from ats.trader.order_types import Order
from ats.trader.trader import Trader

from .backtest_config import BacktestConfig
from .types import Bar

StrategyFn = Callable[[Bar, Trader], Sequence[Order]]


@dataclass
class BacktestResult:
    """Output container for a BacktestEngine run."""

    config: BacktestConfig
    portfolio_history: List[Dict[str, Any]] = field(default_factory=list)
    trade_history: List[Dict[str, Any]] = field(default_factory=list)
    final_portfolio: Optional[Dict[str, Any]] = None
    risk_decisions: List[RiskDecision] = field(default_factory=list)


class BacktestEngine:
    """Backtest engine: loops over bars, calls strategy, routes orders to Trader."""

    def __init__(
        self,
        *,
        config: BacktestConfig,
        trader: Trader,
        bars: Iterable[Bar],
        strategy: StrategyFn,
        risk_manager: RiskManager | None = None,
    ) -> None:
        self.config = config
        self.trader = trader
        self.bars = list(bars)
        self.strategy = strategy
        self.risk_manager = risk_manager

    def run(self) -> BacktestResult:
        """Run the backtest and return the results."""
        result = BacktestResult(config=self.config)

        for i, bar in enumerate(self.bars):
            if self.config.bar_limit is not None and i >= self.config.bar_limit:
                break

            self.trader.update_market({bar.symbol: bar.close})

            candidate_orders = list(self.strategy(bar, self.trader))
            if not candidate_orders:
                continue

            if self.risk_manager is not None:
                decision = self.risk_manager.evaluate_orders(
                    market=bar, orders=candidate_orders
                )
                result.risk_decisions.append(decision)
                orders = list(decision.accepted_orders)
            else:
                orders = candidate_orders

            if not orders:
                continue

            snapshot = self.trader.process_orders(orders)

            portfolio = snapshot.get("portfolio")
            if isinstance(portfolio, dict):
                result.portfolio_history.append(portfolio)
                result.final_portfolio = portfolio

            trades = snapshot.get("trade_history")
            if isinstance(trades, list):
                result.trade_history.extend(trades)

        return result
