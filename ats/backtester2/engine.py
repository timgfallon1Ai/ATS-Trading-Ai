from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from ats.trader.order_types import Order
from ats.trader.trader import Trader

from .backtest_config import BacktestConfig
from .types import Bar

# Strategy signature:
#   strategy(bar: Bar, trader: Trader) -> Sequence[Order]
StrategyFn = Callable[[Bar, Trader], Sequence[Order]]


@dataclass
class BacktestResult:
    """
    Backtest output for analysis + testing.

    portfolio_history:
      - one portfolio snapshot per bar (after marking-to-market),
        regardless of whether a trade occurred.

    trade_history:
      - incremental "fills" (preferred) or incremental deltas from a full ledger.
    """

    config: BacktestConfig
    portfolio_history: List[Dict[str, Any]] = field(default_factory=list)
    trade_history: List[Dict[str, Any]] = field(default_factory=list)
    final_portfolio: Optional[Dict[str, Any]] = None
    risk_decisions: List[Any] = field(default_factory=list)


class BacktestEngine:
    """
    Backtester2 engine:

    - Always marks-to-market every bar
    - Always records a portfolio snapshot every bar
    - Optionally runs RiskManager.evaluate_orders on candidate orders
    - Executes accepted orders through Trader.process_orders
    """

    def __init__(
        self,
        config: BacktestConfig,
        trader: Trader,
        bars: Iterable[Bar],
        strategy: StrategyFn,
        risk_manager: Any = None,
    ) -> None:
        self.config = config
        self.trader = trader
        self._bars = list(bars)
        self.strategy = strategy
        self.risk_manager = risk_manager

    def _market_snapshot(self, bar: Bar) -> Dict[str, float]:
        market = getattr(self.trader, "market", None)
        if market is not None and hasattr(market, "snapshot"):
            try:
                snap = market.snapshot()
                if isinstance(snap, dict):
                    return {str(k): float(v) for k, v in snap.items()}
            except Exception:
                pass
        return {str(bar.symbol): float(bar.close)}

    def _portfolio_snapshot(self, prices: Dict[str, float]) -> Dict[str, Any]:
        portfolio = getattr(self.trader, "portfolio", None)
        if portfolio is not None and hasattr(portfolio, "snapshot"):
            try:
                snap = portfolio.snapshot(prices)
                if isinstance(snap, dict):
                    return snap
            except Exception:
                pass
        if isinstance(portfolio, dict):
            return portfolio
        return {}

    def _coerce_accepted_orders(
        self, decision: Any, fallback: List[Order]
    ) -> List[Order]:
        accepted = None

        if isinstance(decision, dict):
            for key in ("accepted_orders", "safe_orders", "accepted", "orders"):
                if key in decision:
                    accepted = decision[key]
                    break
        else:
            for attr in ("accepted_orders", "safe_orders", "accepted", "orders"):
                if hasattr(decision, attr):
                    accepted = getattr(decision, attr)
                    break

        if accepted is None:
            return fallback

        try:
            return list(accepted)
        except Exception:
            return fallback

    def _evaluate_orders_with_risk(
        self, bar: Bar, candidate: List[Order]
    ) -> Tuple[List[Order], Any]:
        if self.risk_manager is None or not candidate:
            return candidate, None

        fn = getattr(self.risk_manager, "evaluate_orders", None)
        if not callable(fn):
            return candidate, None

        market = self._market_snapshot(bar)
        portfolio = self._portfolio_snapshot(market)
        ts = getattr(bar, "timestamp", None)

        attempts = [
            lambda: fn(
                candidate, bar=bar, market=market, portfolio=portfolio, timestamp=ts
            ),
            lambda: fn(candidate, bar=bar, market=market, portfolio=portfolio),
            lambda: fn(candidate, bar=bar, timestamp=ts),
            lambda: fn(candidate, bar=bar),
            lambda: fn(bar, candidate),
            lambda: fn(candidate),
        ]

        decision = None
        for call in attempts:
            try:
                decision = call()
                break
            except TypeError:
                continue

        if decision is None:
            return candidate, None

        safe = self._coerce_accepted_orders(decision, list(candidate))
        return safe, decision

    def _process_orders(self, orders: Sequence[Order], bar: Bar) -> Any:
        # Backtester bars carry timestamp as string; Trader may accept string or datetime depending on phase.
        try:
            return self.trader.process_orders(
                orders, timestamp=getattr(bar, "timestamp", None)
            )
        except TypeError:
            return self.trader.process_orders(orders)

    def run(self) -> BacktestResult:
        portfolio_history: List[Dict[str, Any]] = []
        trade_history: List[Dict[str, Any]] = []
        risk_decisions: List[Any] = []

        last_ledger_len = 0

        for idx, bar in enumerate(self._bars):
            if self.config.bar_limit is not None and idx >= self.config.bar_limit:
                break

            # Mark-to-market first.
            self.trader.update_market({str(bar.symbol): float(bar.close)})

            # Strategy generates candidate orders (can be empty).
            candidate_orders = list(self.strategy(bar, self.trader))

            # Optional risk layer.
            safe_orders, decision = self._evaluate_orders_with_risk(
                bar, candidate_orders
            )
            if decision is not None:
                risk_decisions.append(decision)

            # Always call trader, even if safe_orders is empty, so we snapshot per bar.
            result = self._process_orders(safe_orders, bar)

            prices = self._market_snapshot(bar)

            if isinstance(result, dict):
                # Portfolio snapshot
                port = result.get("portfolio")
                if isinstance(port, dict):
                    port_entry = dict(port)
                else:
                    port_entry = dict(self._portfolio_snapshot(prices))

                if "timestamp" not in port_entry:
                    port_entry["timestamp"] = getattr(bar, "timestamp", None)
                portfolio_history.append(port_entry)

                # Incremental fills (preferred)
                fills = result.get("fills")
                if isinstance(fills, list) and fills:
                    for f in fills:
                        trade_history.append(f if isinstance(f, dict) else {"fill": f})
                else:
                    # Fallback: derive incremental trades from a full ledger list
                    ledger = result.get("trade_history")
                    if isinstance(ledger, list):
                        new = ledger[last_ledger_len:]
                        for t in new:
                            trade_history.append(
                                t if isinstance(t, dict) else {"trade": t}
                            )
                        last_ledger_len = len(ledger)
            else:
                # Worst-case: still snapshot portfolio
                port_entry = dict(self._portfolio_snapshot(prices))
                if "timestamp" not in port_entry:
                    port_entry["timestamp"] = getattr(bar, "timestamp", None)
                portfolio_history.append(port_entry)

        final_portfolio = portfolio_history[-1] if portfolio_history else None

        return BacktestResult(
            config=self.config,
            portfolio_history=portfolio_history,
            trade_history=trade_history,
            final_portfolio=final_portfolio,
            risk_decisions=risk_decisions,
        )
