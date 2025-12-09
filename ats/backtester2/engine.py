from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Sequence

from ats.trader.trader import Trader
from ats.trader.order_types import Order
from ats.risk_manager import RiskDecision, RiskManager

from .backtest_config import BacktestConfig
from .types import Bar


# Strategy function signature:
#     strategy(bar: Bar, trader: Trader) -> Sequence[Order]
StrategyFn = Callable[[Bar, Trader], Sequence[Order]]


@dataclass
class BacktestResult:
    """
    Result of a backtest run.

    - config: The BacktestConfig used for this run.
    - portfolio_history: List of portfolio snapshots returned from Trader.
    - trade_history: Aggregate of trade history objects returned from Trader.
    - final_portfolio: The last portfolio snapshot, or None if no trades.
    - risk_decisions: Optional list of RiskDecision objects, one per bar
      where orders were evaluated by the RiskManager.
    """

    config: BacktestConfig
    portfolio_history: List[Dict[str, Any]] = field(default_factory=list)
    trade_history: List[Any] = field(default_factory=list)
    final_portfolio: Dict[str, Any] | None = None
    risk_decisions: List[RiskDecision] = field(default_factory=list)


class BacktestEngine:
    """
    Minimal v2 backtest engine with baseline risk integration.

    This engine:

    - Iterates over a sequence of Bar objects.
    - For each bar, updates the Trader's market prices.
    - Calls a user-provided StrategyFn to generate orders.
    - Optionally passes those orders through a RiskManager.
    - Sends the accepted orders to Trader.process_orders().
    - Records portfolio snapshots and trades from the Trader result dict.
    """

    def __init__(
        self,
        config: BacktestConfig,
        trader: Trader,
        bars: Iterable[Bar],
        strategy: StrategyFn,
        risk_manager: RiskManager | None = None,
    ) -> None:
        self.config = config
        self.trader = trader
        self._bars = list(bars)
        self.strategy = strategy
        self.risk_manager = risk_manager

    def run(self) -> BacktestResult:
        portfolio_history: List[Dict[str, Any]] = []
        trade_history: List[Any] = []
        risk_decisions: List[RiskDecision] = []

        for idx, bar in enumerate(self._bars):
            if self.config.bar_limit is not None and idx >= self.config.bar_limit:
                break

            # Mark the trader to market for this bar's close price.
            self.trader.update_market({bar.symbol: bar.close})

            # Let the strategy decide what to do at this bar.
            orders: Sequence[Order] = self.strategy(bar, self.trader)
            if not orders:
                # No action for this bar.
                continue

            candidate_orders = list(orders)

            # Apply baseline risk management if present.
            if self.risk_manager is not None:
                decision = self.risk_manager.evaluate_orders(bar, candidate_orders)
                safe_orders = list(decision.accepted_orders)

                # Record the decision even if no orders survive.
                risk_decisions.append(decision)

                if not safe_orders:
                    # All orders were blocked by risk.
                    continue
            else:
                safe_orders = candidate_orders

            result = self.trader.process_orders(safe_orders)

            # We expect Trader.process_orders to return a dict-like structure,
            # but we keep the contract loose to avoid coupling to internals.
            if isinstance(result, dict):
                portfolio = result.get("portfolio")
                if portfolio is not None:
                    portfolio_history.append(portfolio)

                trades = result.get("trade_history")
                if trades:
                    # Could be list or single object; normalize to list.
                    if isinstance(trades, list):
                        trade_history.extend(trades)
                    else:
                        trade_history.append(trades)

        final_portfolio = portfolio_history[-1] if portfolio_history else None

        return BacktestResult(
            config=self.config,
            portfolio_history=portfolio_history,
            trade_history=trade_history,
            final_portfolio=final_portfolio,
            risk_decisions=risk_decisions,
        )
