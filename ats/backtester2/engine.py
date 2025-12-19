from __future__ import annotations

from dataclasses import dataclass
import inspect
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

from ats.risk_manager import RiskDecision, RiskManager
from ats.trader.order_types import Order
from ats.trader.trader import Trader

from .backtest_config import BacktestConfig
from .types import Bar

StrategyFn = Callable[[Bar, Trader], Sequence[Order]]


@dataclass(frozen=True)
class BacktestResult:
    """
    Results returned from BacktestEngine.run().

    Notes:
      - portfolio_history only appends when Trader returns a dict snapshot that includes
        a "portfolio" key (to keep coupling loose).
      - trade_history similarly pulls from "trade_history" if present.
      - risk_decisions records each RiskManager decision for auditability.
    """

    config: BacktestConfig
    portfolio_history: List[Dict[str, Any]]
    trade_history: List[Any]
    final_portfolio: Optional[Dict[str, Any]]
    risk_decisions: List[RiskDecision]


class BacktestEngine:
    """
    Minimal, deterministic backtest loop that wires:

      bars -> strategy(bar, trader) -> (optional) risk_manager -> trader.process_orders()

    The key contract:
      RiskManager.evaluate_orders(bar, orders) -> RiskDecision
        - accepted_orders: orders allowed through
        - rejected_orders: orders blocked (with reasons / metadata handled inside RM)
    """

    def __init__(
        self,
        config: BacktestConfig,
        trader: Trader,
        bars: Iterable[Bar],
        strategy: StrategyFn,
        risk_manager: Optional[RiskManager] = None,
    ) -> None:
        self.config = config
        self.trader = trader
        self._bars = list(bars)
        self.strategy = strategy
        self.risk_manager = risk_manager

    def _process_orders_with_optional_timestamp(
        self, orders: Sequence[Order], bar: Bar
    ) -> Any:
        """
        Call Trader.process_orders in a way that works whether it supports
        a timestamp kwarg or not.

        This keeps the backtester compatible across small Trader API changes
        while still preferring deterministic timestamps when available.
        """
        fn = self.trader.process_orders
        try:
            sig = inspect.signature(fn)
            if "timestamp" in sig.parameters:
                return fn(orders, timestamp=bar.timestamp)
        except (TypeError, ValueError):
            # Some callables may not support signature inspection.
            pass
        return fn(orders)

    def run(self) -> BacktestResult:
        portfolio_history: List[Dict[str, Any]] = []
        trade_history: List[Any] = []
        risk_decisions: List[RiskDecision] = []

        for idx, bar in enumerate(self._bars):
            if self.config.bar_limit is not None and idx >= self.config.bar_limit:
                break

            # Mark-to-market the trader for this bar's close price.
            self.trader.update_market({bar.symbol: bar.close})

            # Strategy decides candidate orders for this bar.
            orders: Sequence[Order] = self.strategy(bar, self.trader)
            if not orders:
                continue

            candidate_orders = list(orders)

            # Apply risk gating (Phase 3): evaluate_orders(bar, candidate_orders)
            if self.risk_manager is not None:
                decision = self.risk_manager.evaluate_orders(bar, candidate_orders)
                risk_decisions.append(decision)

                safe_orders = list(decision.accepted_orders)
                if not safe_orders:
                    # All orders blocked by risk.
                    continue
            else:
                safe_orders = candidate_orders

            # Execute orders through the Trader.
            result = self._process_orders_with_optional_timestamp(safe_orders, bar)

            # Keep coupling loose: only extract fields if result is dict-like.
            if isinstance(result, dict):
                portfolio = result.get("portfolio")
                if portfolio is not None:
                    portfolio_history.append(portfolio)

                trades = result.get("trade_history")
                if trades:
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
