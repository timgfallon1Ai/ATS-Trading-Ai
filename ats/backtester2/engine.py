from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from ats.risk_manager.risk_manager import RiskDecision, RiskManager
from ats.trader.order_types import Order
from ats.trader.trader import Trader

from .backtest_config import BacktestConfig
from .types import Bar

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    config: BacktestConfig
    portfolio_history: List[Dict[str, Any]] = field(default_factory=list)
    trade_history: List[Any] = field(default_factory=list)
    final_portfolio: Optional[Dict[str, Any]] = None
    risk_decisions: List[Any] = field(default_factory=list)


class BacktestEngine:
    def __init__(
        self,
        config: BacktestConfig,
        trader: Trader,
        bars: Sequence[Bar],
        strategy: Any,
        risk_manager: Optional[RiskManager] = None,
    ) -> None:
        self.config = config
        self.trader = trader
        self.strategy = strategy
        self.risk_manager = risk_manager
        self._bars = list(bars)

    # ---------------------------
    # Kill-switch helpers
    # ---------------------------

    def _kill_switch_path(self) -> Optional[Path]:
        """
        Prefer ATS_KILL_SWITCH_FILE when set (unit tests set this).
        Fallback (best-effort) to ATS_LOG_DIR/KILL_SWITCH for CLI parity.
        """
        raw = os.getenv("ATS_KILL_SWITCH_FILE")
        if raw:
            try:
                return Path(raw)
            except Exception:
                return None

        log_dir = os.getenv("ATS_LOG_DIR")
        if log_dir:
            try:
                return Path(log_dir) / "KILL_SWITCH"
            except Exception:
                return None

        return None

    def _is_kill_switch_engaged(self) -> bool:
        """
        Engage if the kill switch file exists.
        """
        # Prefer the backtester2 module if present (keeps semantics aligned with tests),
        # but never fail hard if it can't be imported.
        try:
            from .kill_switch import is_kill_switch_engaged  # type: ignore

            return bool(is_kill_switch_engaged())
        except Exception:
            pass

        p = self._kill_switch_path()
        if not p:
            return False
        try:
            return p.exists()
        except Exception:
            return False

    # ---------------------------
    # Market / portfolio snapshots
    # ---------------------------

    def _market_snapshot(self, bar: Bar) -> Dict[str, float]:
        mkt = getattr(self.trader, "market", None)
        snap_fn = getattr(mkt, "snapshot", None)
        if callable(snap_fn):
            try:
                v = snap_fn()
                if isinstance(v, dict):
                    out: Dict[str, float] = {}
                    for k, vv in v.items():
                        try:
                            out[str(k)] = float(vv)
                        except Exception:
                            continue
                    if out:
                        return out
            except Exception:
                pass

        # Fallback: bar close
        try:
            return {str(bar.symbol): float(bar.close)}
        except Exception:
            return {}

    def _portfolio_snapshot(self, prices: Dict[str, float]) -> Dict[str, Any]:
        portfolio = getattr(self.trader, "portfolio", None)
        snap_fn = getattr(portfolio, "snapshot", None)
        if callable(snap_fn):
            try:
                v = snap_fn(prices)
                if isinstance(v, dict):
                    return dict(v)
            except TypeError:
                # Some older snapshot() signatures may not accept prices
                try:
                    v2 = snap_fn()
                    if isinstance(v2, dict):
                        return dict(v2)
                except Exception:
                    pass
            except Exception:
                pass

        # Best-effort fallback: empty snapshot
        return {}

    # ---------------------------
    # Order coercion / strategy
    # ---------------------------

    def _coerce_order(self, obj: Any) -> Optional[Order]:
        if obj is None:
            return None
        if isinstance(obj, Order):
            return obj

        # dict-like
        if isinstance(obj, dict):
            try:
                symbol = str(obj.get("symbol"))
                side = str(obj.get("side"))
                size_raw = obj.get("size", obj.get("qty", obj.get("quantity", 0.0)))
                size = float(size_raw)
                order_type = str(obj.get("order_type", "market"))
                return Order(symbol=symbol, side=side, size=size, order_type=order_type)
            except Exception:
                return None

        # attribute-like
        try:
            symbol = getattr(obj, "symbol", None)
            side = getattr(obj, "side", None)
            size_raw = getattr(obj, "size", None)
            if size_raw is None:
                size_raw = getattr(obj, "qty", None)
            if size_raw is None:
                size_raw = getattr(obj, "quantity", None)
            order_type = getattr(obj, "order_type", "market")

            if symbol is None or side is None or size_raw is None:
                return None

            return Order(
                symbol=str(symbol),
                side=str(side),
                size=float(size_raw),
                order_type=str(order_type),
            )
        except Exception:
            return None

    def _strategy_orders(self, bar: Bar) -> List[Order]:
        out: Any = None
        try:
            strategy_fn = getattr(self.strategy, "on_bar", None)
            if callable(strategy_fn):
                out = strategy_fn(bar, self.trader)
            else:
                # Strategy may be a plain callable(bar, trader)
                out = self.strategy(bar, self.trader)
        except Exception:
            logger.exception("Strategy evaluation failed; skipping bar.")
            return []

        if out is None:
            return []

        if isinstance(out, list):
            orders: List[Order] = []
            for item in out:
                o = self._coerce_order(item)
                if o is not None:
                    orders.append(o)
            return orders

        single = self._coerce_order(out)
        return [single] if single is not None else []

    # ---------------------------
    # Risk + execution
    # ---------------------------

    def _evaluate_orders_with_risk(
        self, orders: List[Order], prices: Dict[str, float], bar: Bar
    ) -> Tuple[List[Order], Optional[RiskDecision]]:
        if not self.risk_manager or not orders:
            return orders, None

        ctx = {
            "prices": prices,
            "bar": bar,
            "portfolio": self._portfolio_snapshot(prices),
        }

        try:
            decision = self.risk_manager.evaluate_orders(orders, ctx)
        except Exception:
            logger.exception(
                "RiskManager.evaluate_orders failed; passing orders through."
            )
            return orders, None

        # Accept both dict-based and object-based decisions
        accepted = None
        if isinstance(decision, dict):
            accepted = decision.get("accepted_orders", None)
        else:
            accepted = getattr(decision, "accepted_orders", None)

        safe: List[Order] = []
        if isinstance(accepted, list):
            for item in accepted:
                o = self._coerce_order(item)
                if o is not None:
                    safe.append(o)

        # If decision doesn't provide accepted_orders, treat as pass-through
        if not safe and accepted is None:
            safe = orders

        return safe, decision

    def _safe_update_market(self, prices: Dict[str, float], bar: Bar) -> None:
        update_market = getattr(self.trader, "update_market", None)
        if not callable(update_market):
            return
        try:
            update_market(prices, timestamp=getattr(bar, "timestamp", None))
        except TypeError:
            # older signature
            try:
                update_market(prices)
            except Exception:
                logger.exception("Trader.update_market failed (fallback).")
        except Exception:
            logger.exception("Trader.update_market failed.")

    def _process_orders(self, orders: List[Order], bar: Bar) -> Dict[str, Any]:
        process_orders = getattr(self.trader, "process_orders", None)
        if not callable(process_orders):
            return {
                "portfolio": self._portfolio_snapshot(self._market_snapshot(bar)),
                "fills": [],
            }

        try:
            result = process_orders(orders, timestamp=getattr(bar, "timestamp", None))
            return result if isinstance(result, dict) else {"result": result}
        except TypeError:
            # older signature
            try:
                result = process_orders(orders)
                return result if isinstance(result, dict) else {"result": result}
            except Exception:
                logger.exception("Trader.process_orders failed (fallback).")
                return {
                    "portfolio": self._portfolio_snapshot(self._market_snapshot(bar)),
                    "fills": [],
                }
        except Exception:
            logger.exception("Trader.process_orders failed.")
            return {
                "portfolio": self._portfolio_snapshot(self._market_snapshot(bar)),
                "fills": [],
            }

    # ---------------------------
    # Flatten logic (kill-switch)
    # ---------------------------

    def _extract_position_quantities(
        self, portfolio_snap: Dict[str, Any]
    ) -> Dict[str, float]:
        pos = portfolio_snap.get("positions", None)
        out: Dict[str, float] = {}

        if isinstance(pos, dict):
            for sym, v in pos.items():
                qty_val: Any = None
                if isinstance(v, dict):
                    qty_val = v.get("quantity", v.get("qty", v.get("position")))
                else:
                    qty_val = v
                try:
                    qty = float(qty_val)
                except Exception:
                    continue
                out[str(sym)] = qty

        return out

    def _build_flatten_orders(self, prices: Dict[str, float]) -> List[Order]:
        snap = self._portfolio_snapshot(prices)
        qtys = self._extract_position_quantities(snap)

        orders: List[Order] = []
        for sym, qty in qtys.items():
            if abs(qty) < 1e-9:
                continue
            side = "sell" if qty > 0 else "buy"
            orders.append(
                Order(symbol=sym, side=side, size=float(abs(qty)), order_type="market")
            )
        return orders

    # ---------------------------
    # Main loop
    # ---------------------------

    def run(self) -> BacktestResult:
        portfolio_history: List[Dict[str, Any]] = []
        trade_history: List[Any] = []
        risk_decisions: List[Any] = []

        last_ledger_len = 0

        for i, bar in enumerate(self._bars):
            # Respect bar_limit if set
            bar_limit = getattr(self.config, "bar_limit", None)
            if bar_limit is not None and i >= int(bar_limit):
                break

            # Mark-to-market first
            prices = self._market_snapshot(bar)
            if prices:
                self._safe_update_market(prices, bar)
                prices = self._market_snapshot(bar)

            # Kill-switch check MUST happen before calling strategy on this bar
            if self._is_kill_switch_engaged():
                flatten_orders = self._build_flatten_orders(prices)
                result = self._process_orders(flatten_orders, bar)

                snap = result.get("portfolio")
                if not isinstance(snap, dict):
                    snap = self._portfolio_snapshot(prices)
                snap = dict(snap) if isinstance(snap, dict) else {}
                if "timestamp" not in snap:
                    snap["timestamp"] = getattr(bar, "timestamp", None)
                portfolio_history.append(snap)

                ledger = getattr(self.trader, "ledger", None)
                if isinstance(ledger, list):
                    new_items = ledger[last_ledger_len:]
                    last_ledger_len = len(ledger)
                    if new_items:
                        trade_history.extend(new_items)

                fills = result.get("fills")
                if isinstance(fills, list) and fills:
                    trade_history.extend(fills)

                # Stop immediately after flattening
                break

            # Normal path: strategy -> risk -> execute
            candidate_orders = self._strategy_orders(bar)
            safe_orders, decision = self._evaluate_orders_with_risk(
                candidate_orders, prices, bar
            )
            if decision is not None:
                risk_decisions.append(decision)

            result = self._process_orders(safe_orders, bar)

            snap = result.get("portfolio")
            if not isinstance(snap, dict):
                snap = self._portfolio_snapshot(prices)
            snap = dict(snap) if isinstance(snap, dict) else {}
            if "timestamp" not in snap:
                snap["timestamp"] = getattr(bar, "timestamp", None)
            portfolio_history.append(snap)

            ledger = getattr(self.trader, "ledger", None)
            if isinstance(ledger, list):
                new_items = ledger[last_ledger_len:]
                last_ledger_len = len(ledger)
                if new_items:
                    trade_history.extend(new_items)

            fills = result.get("fills")
            if isinstance(fills, list) and fills:
                trade_history.extend(fills)

        final_portfolio = portfolio_history[-1] if portfolio_history else None
        return BacktestResult(
            config=self.config,
            portfolio_history=portfolio_history,
            trade_history=trade_history,
            final_portfolio=final_portfolio,
            risk_decisions=risk_decisions,
        )
