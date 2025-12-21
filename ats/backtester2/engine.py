from __future__ import annotations

from dataclasses import dataclass
import inspect
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

from ats.core.kill_switch import kill_switch_engaged
from ats.risk_manager import RiskDecision, RiskManager
from ats.trader.order_types import Order
from ats.trader.trader import Trader

from .backtest_config import BacktestConfig
from .types import Bar

StrategyFn = Callable[[Bar, Trader], Sequence[Order]]


@dataclass(frozen=True)
class BacktestResult:
    config: BacktestConfig
    portfolio_history: List[Dict[str, Any]]
    trade_history: List[Any]
    final_portfolio: Optional[Dict[str, Any]]
    risk_decisions: List[RiskDecision]


class BacktestEngine:
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

    def _safe_market_snapshot(self) -> Dict[str, float]:
        market = getattr(self.trader, "market", None)
        if market is not None and hasattr(market, "snapshot"):
            try:
                snap = market.snapshot()
                if isinstance(snap, dict):
                    return {str(k): float(v) for k, v in snap.items()}
            except Exception:
                pass
        return {}

    def _safe_portfolio_snapshot(
        self, prices: Dict[str, float]
    ) -> Optional[Dict[str, Any]]:
        portfolio = getattr(self.trader, "portfolio", None)
        if portfolio is None:
            return None
        if hasattr(portfolio, "snapshot"):
            try:
                snap = portfolio.snapshot(prices)
                if isinstance(snap, dict):
                    return snap
            except Exception:
                return None
        return None

    def _process_orders_with_optional_timestamp(
        self, orders: Sequence[Order], bar: Bar
    ) -> Any:
        fn = self.trader.process_orders
        try:
            sig = inspect.signature(fn)
            if "timestamp" in sig.parameters:
                return fn(orders, timestamp=bar.timestamp)
        except (TypeError, ValueError):
            pass
        return fn(orders)

    def _record_trader_result(
        self,
        result: Any,
        *,
        portfolio_history: List[Dict[str, Any]],
        trade_history: List[Any],
    ) -> Optional[Dict[str, Any]]:
        if not isinstance(result, dict):
            return None

        portfolio = result.get("portfolio")
        if isinstance(portfolio, dict):
            portfolio_history.append(portfolio)

        trades = result.get("trade_history")
        if trades:
            if isinstance(trades, list):
                trade_history.extend(trades)
            else:
                trade_history.append(trades)

        return portfolio if isinstance(portfolio, dict) else None

    def run(self) -> BacktestResult:
        portfolio_history: List[Dict[str, Any]] = []
        trade_history: List[Any] = []
        risk_decisions: List[RiskDecision] = []

        for idx, bar in enumerate(self._bars):
            if self.config.bar_limit is not None and idx >= self.config.bar_limit:
                break

            # Update market first (so flatten uses current bar close).
            self.trader.update_market({bar.symbol: bar.close})

            prices = self._safe_market_snapshot()
            if bar.symbol not in prices:
                prices[bar.symbol] = float(bar.close)

            portfolio_snapshot = self._safe_portfolio_snapshot(prices)

            # ------------------------------------------------------------------
            # Phase9.3 kill-switch: checked every bar ("orchestrator cycle")
            # If engaged: flatten positions and stop.
            # ------------------------------------------------------------------
            if kill_switch_engaged():
                result = self.trader.flatten_positions(
                    timestamp=bar.timestamp, meta_reason="kill_switch"
                )
                self._record_trader_result(
                    result,
                    portfolio_history=portfolio_history,
                    trade_history=trade_history,
                )
                break

            candidate_orders = list(self.strategy(bar, self.trader))
            if not candidate_orders:
                # Still record portfolio periodically if you want; currently we keep minimal.
                continue

            if self.risk_manager is not None:
                decision = self.risk_manager.evaluate_orders(
                    bar,
                    candidate_orders,
                    portfolio=portfolio_snapshot,
                )
                risk_decisions.append(decision)
                safe_orders = list(decision.accepted_orders)
                if not safe_orders:
                    continue
            else:
                safe_orders = candidate_orders

            result = self._process_orders_with_optional_timestamp(safe_orders, bar)
            last_portfolio = self._record_trader_result(
                result,
                portfolio_history=portfolio_history,
                trade_history=trade_history,
            )

            # ------------------------------------------------------------------
            # If portfolio is halted (principal floor breach), flatten and stop.
            # ------------------------------------------------------------------
            if isinstance(last_portfolio, dict) and bool(last_portfolio.get("halted")):
                flat = self.trader.flatten_positions(
                    timestamp=bar.timestamp, meta_reason="portfolio_halted"
                )
                self._record_trader_result(
                    flat,
                    portfolio_history=portfolio_history,
                    trade_history=trade_history,
                )
                break

        final_portfolio = portfolio_history[-1] if portfolio_history else None
        return BacktestResult(
            config=self.config,
            portfolio_history=portfolio_history,
            trade_history=trade_history,
            final_portfolio=final_portfolio,
            risk_decisions=risk_decisions,
        )
