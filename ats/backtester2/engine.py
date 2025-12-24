from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ats.backtester2.backtest_config import BacktestConfig
from ats.backtester2.types import Bar

try:
    # Newer location (added in phase14)
    from ats.trader.order import Order
except Exception:  # pragma: no cover
    # Older location
    from ats.trader.order_types import Order  # type: ignore

from ats.trader.trader import Trader

try:
    # Prefer backtester2 wrapper if present (tests may import this).
    from ats.backtester2.kill_switch import (  # type: ignore
        kill_switch_engaged,
        read_kill_switch_state,
    )
except Exception:  # pragma: no cover
    try:
        # Fallback to core kill-switch implementation.
        from ats.core.kill_switch import (  # type: ignore
            kill_switch_engaged,
            read_kill_switch_state,
        )
    except Exception:  # pragma: no cover

        def kill_switch_engaged() -> bool:  # type: ignore
            return False

        def read_kill_switch_state() -> Any:  # type: ignore
            return None


try:
    from ats.risk_manager.risk_manager import RiskManager
except Exception:  # pragma: no cover
    RiskManager = Any  # type: ignore[misc,assignment]


logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """
    Backtest output container.

    Tests require:
      - `res.config.symbol` to exist
      - `portfolio_history` to record per bar (unless halted early)
    """

    config: BacktestConfig
    portfolio_history: List[Dict[str, Any]] = field(default_factory=list)
    trade_history: List[Dict[str, Any]] = field(default_factory=list)
    final_portfolio: Optional[Dict[str, Any]] = None
    risk_decisions: List[Any] = field(default_factory=list)

    # Optional metadata
    halted: bool = False
    halted_reason: Optional[str] = None

    @property
    def symbol(self) -> str:
        return str(getattr(self.config, "symbol", ""))


@dataclass
class BacktestEngine:
    config: BacktestConfig
    trader: Trader
    bars: Sequence[Bar]
    strategy: Any
    risk_manager: Optional[RiskManager] = None

    # ----- helpers -----

    def _market_snapshot(self, bar: Bar) -> Dict[str, float]:
        """
        Return a mapping {symbol: price} for mark-to-market. Prefer Trader.market.snapshot()
        if present; otherwise derive from the bar.
        """
        sym = str(getattr(bar, "symbol", getattr(self.config, "symbol", "")))
        px = float(getattr(bar, "close", getattr(bar, "price", 0.0)) or 0.0)

        market = getattr(self.trader, "market", None)
        snap = getattr(market, "snapshot", None)
        if callable(snap):
            try:
                out = snap()
                if isinstance(out, dict):
                    return {str(k): float(v) for k, v in out.items()}
            except Exception:  # pragma: no cover
                logger.exception("Market.snapshot() failed; falling back to bar price")

        return {sym: px}

    def _portfolio_snapshot(self, prices: Dict[str, float]) -> Dict[str, Any]:
        """
        Return a dict portfolio snapshot. Some implementations require prices as a param.
        """
        portfolio = getattr(self.trader, "portfolio", None)
        snap = getattr(portfolio, "snapshot", None)
        if callable(snap):
            try:
                return dict(snap(prices))  # type: ignore[arg-type]
            except TypeError:
                # Older signature
                return dict(snap())  # type: ignore[misc]
            except Exception:  # pragma: no cover
                logger.exception(
                    "Portfolio.snapshot() failed; returning empty snapshot"
                )

        return {}

    def _evaluate_orders_with_risk(
        self, bar: Bar, candidate: Sequence[Order]
    ) -> Tuple[List[Order], Optional[Any]]:
        """Run risk manager if present; otherwise return candidate."""
        if not candidate or self.risk_manager is None:
            return list(candidate), None

        rm = self.risk_manager
        decision = None

        # Try common method names; support both old and new signatures.
        for name in ("evaluate_orders", "evaluate", "filter_orders"):
            fn = getattr(rm, name, None)
            if not callable(fn):
                continue
            try:
                decision = fn(list(candidate), bar=bar, trader=self.trader)  # type: ignore[misc]
                break
            except TypeError:
                try:
                    decision = fn(list(candidate))  # type: ignore[misc]
                    break
                except Exception:  # pragma: no cover
                    logger.exception("RiskManager.%s failed", name)
                    decision = None
                    break
            except Exception:  # pragma: no cover
                logger.exception("RiskManager.%s failed", name)
                decision = None
                break

        if decision is None:
            return list(candidate), None

        # Accept either an iterable of orders, a dict with "accepted_orders", or a custom object.
        accepted: List[Order] = []
        if isinstance(decision, dict):
            maybe = decision.get("accepted_orders", decision.get("orders"))
            if maybe is None:
                accepted = list(candidate)
            elif isinstance(maybe, list):
                accepted = [o for o in maybe if o]
            else:
                try:
                    accepted = list(maybe)  # type: ignore[arg-type]
                except Exception:
                    accepted = list(candidate)
        else:
            maybe = getattr(decision, "accepted_orders", None)
            if maybe is None:
                accepted = list(candidate)
            elif isinstance(maybe, list):
                accepted = [o for o in maybe if o]
            else:
                try:
                    accepted = list(maybe)  # type: ignore[arg-type]
                except Exception:
                    accepted = list(candidate)

        return accepted, decision

    def _process_orders(self, orders: Sequence[Order], bar: Bar) -> Any:
        """Send orders to Trader, handling old/new signatures."""
        ts = getattr(bar, "timestamp", None)
        try:
            return self.trader.process_orders(list(orders), timestamp=ts)  # type: ignore[arg-type]
        except TypeError:
            return self.trader.process_orders(list(orders))  # type: ignore[arg-type]

    def _append_from_trader_result(
        self,
        result: Any,
        bar: Bar,
        prices: Dict[str, float],
        portfolio_history: List[Dict[str, Any]],
        trade_history: List[Dict[str, Any]],
        last_ledger_len: int,
    ) -> int:
        """Normalize trader output to portfolio_history + trade_history; returns updated ledger index."""
        # Portfolio snapshot (always)
        port_entry: Dict[str, Any] = {}
        if isinstance(result, dict):
            port = result.get("portfolio")
            if isinstance(port, dict):
                port_entry = dict(port)
            else:
                port_entry = dict(self._portfolio_snapshot(prices))
        else:
            port_entry = dict(self._portfolio_snapshot(prices))

        if "timestamp" not in port_entry:
            port_entry["timestamp"] = getattr(bar, "timestamp", None)
        portfolio_history.append(port_entry)

        # Trades/fills
        if isinstance(result, dict):
            fills = result.get("fills")
            if isinstance(fills, list) and fills:
                for f in fills:
                    trade_history.append(f if isinstance(f, dict) else {"fill": f})
                return last_ledger_len

            ledger = result.get("trade_history")
            if isinstance(ledger, list):
                new = ledger[last_ledger_len:]
                for t in new:
                    trade_history.append(t if isinstance(t, dict) else {"trade": t})
                return len(ledger)

        return last_ledger_len

    def _build_flatten_orders(self, prices: Dict[str, float]) -> List[Order]:
        """Build market orders that flatten all open positions."""
        snap = self._portfolio_snapshot(prices)
        positions = snap.get("positions", {}) if isinstance(snap, dict) else {}
        if not isinstance(positions, dict):
            return []

        orders: List[Order] = []
        for sym, pos in positions.items():
            qty = 0.0
            if isinstance(pos, dict):
                qty = float(pos.get("quantity", pos.get("qty", 0.0)) or 0.0)
            else:
                try:
                    qty = float(
                        getattr(pos, "quantity", getattr(pos, "qty", 0.0)) or 0.0
                    )
                except Exception:
                    qty = 0.0

            if abs(qty) < 1e-9:
                continue

            side = "sell" if qty > 0 else "buy"
            orders.append(
                Order(
                    symbol=str(sym),
                    side=side,
                    size=float(abs(qty)),
                    order_type="market",
                )
            )
        return orders

    def _kill_switch_reason(self) -> Optional[str]:
        try:
            st = read_kill_switch_state()
            return (
                getattr(st, "reason", None)
                or getattr(st, "message", None)
                or getattr(st, "detail", None)
            )
        except Exception:  # pragma: no cover
            return None

    # ----- main loop -----

    def run(self) -> BacktestResult:
        portfolio_history: List[Dict[str, Any]] = []
        trade_history: List[Dict[str, Any]] = []
        risk_decisions: List[Any] = []

        last_ledger_len = 0
        halted = False
        halted_reason: Optional[str] = None

        for idx, bar in enumerate(self.bars):
            if self.config.bar_limit is not None and idx >= self.config.bar_limit:
                break

            # Mark-to-market first.
            self.trader.update_market({str(bar.symbol): float(bar.close)})

            # Kill-switch check: if engaged, flatten and stop BEFORE calling strategy on this bar.
            if kill_switch_engaged():
                halted = True
                halted_reason = self._kill_switch_reason() or "kill_switch"

                prices = self._market_snapshot(bar)

                flatten_orders = self._build_flatten_orders(prices)
                if flatten_orders:
                    result = self._process_orders(flatten_orders, bar)
                    last_ledger_len = self._append_from_trader_result(
                        result,
                        bar,
                        prices,
                        portfolio_history,
                        trade_history,
                        last_ledger_len,
                    )
                else:
                    # No positions to flatten; still record a snapshot for this bar.
                    last_ledger_len = self._append_from_trader_result(
                        {},
                        bar,
                        prices,
                        portfolio_history,
                        trade_history,
                        last_ledger_len,
                    )

                break

            # Strategy generates candidate orders (can be empty).
            try:
                out = self.strategy(bar, self.trader)
            except Exception:  # pragma: no cover
                logger.exception("Strategy failed; treating as no-orders")
                out = []

            candidate_orders: List[Order]
            if out is None:
                candidate_orders = []
            elif isinstance(out, Order):
                candidate_orders = [out]
            elif isinstance(out, list):
                candidate_orders = [o for o in out if o]
            elif isinstance(out, dict):
                maybe = out.get("orders") or out.get("accepted_orders")
                if maybe is None:
                    candidate_orders = []
                elif isinstance(maybe, list):
                    candidate_orders = [o for o in maybe if o]
                else:
                    try:
                        candidate_orders = [o for o in list(maybe) if o]  # type: ignore[arg-type]
                    except TypeError:
                        candidate_orders = []
            else:
                # If it's an iterator/generator, list() it. If it's a single order-like object, wrap it.
                try:
                    candidate_orders = [o for o in list(out) if o]  # type: ignore[arg-type]
                except TypeError:
                    candidate_orders = [out]  # type: ignore[list-item]

            # Optional risk layer.
            safe_orders, decision = self._evaluate_orders_with_risk(
                bar, candidate_orders
            )
            if decision is not None:
                risk_decisions.append(decision)

            # Always call trader, even if safe_orders is empty, so we snapshot per bar.
            result = self._process_orders(safe_orders, bar)

            prices = self._market_snapshot(bar)
            last_ledger_len = self._append_from_trader_result(
                result, bar, prices, portfolio_history, trade_history, last_ledger_len
            )

        final_portfolio = portfolio_history[-1] if portfolio_history else None

        return BacktestResult(
            config=self.config,
            portfolio_history=portfolio_history,
            trade_history=trade_history,
            final_portfolio=final_portfolio,
            risk_decisions=risk_decisions,
            halted=halted,
            halted_reason=halted_reason,
        )
