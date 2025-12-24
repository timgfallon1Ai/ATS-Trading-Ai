from __future__ import annotations

import importlib
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

from .backtest_config import BacktestConfig
from .types import Bar

logger = logging.getLogger(__name__)

# Strategy callback: (bar, trader) -> iterable[Order]
# Kept as Any to avoid coupling to a single Order type implementation.
StrategyFn = Callable[[Bar, Any], Iterable[Any]]


@dataclass
class BacktestResult:
    portfolio_history: List[Dict[str, Any]] = field(default_factory=list)
    trade_history: List[Dict[str, Any]] = field(default_factory=list)
    final_portfolio: Dict[str, Any] = field(default_factory=dict)
    risk_decisions: List[Dict[str, Any]] = field(default_factory=list)


def _kill_switch_enabled() -> bool:
    """
    Best-effort kill switch check.

    - If ats.backtester2.kill_switch exists and exposes is_enabled(), use it.
    - Otherwise, fall back to an environment toggle.
    """
    try:
        mod = importlib.import_module("ats.backtester2.kill_switch")
        fn = getattr(mod, "is_enabled", None)
        if callable(fn):
            return bool(fn())
    except Exception:
        pass

    return os.environ.get("ATS_KILL_SWITCH", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


class BacktestEngine:
    """
    Backtester2 engine that drives a Trader over a sequence of Bars.

    Phase 14 / Metrics requirements:
      - record a portfolio snapshot for *every bar*
      - each snapshot includes at least: timestamp, equity
    """

    def __init__(
        self,
        *,
        config: BacktestConfig,
        trader: Any,
        bars: Sequence[Bar],
        strategy: StrategyFn,
        risk_manager: Optional[Any] = None,
    ) -> None:
        self.config = config
        self.trader = trader
        self.bars = list(bars)
        self.strategy = strategy
        self.risk_manager = risk_manager

    def run(self) -> BacktestResult:
        portfolio_history: List[Dict[str, Any]] = []
        trade_history: List[Dict[str, Any]] = []
        risk_decisions: List[Dict[str, Any]] = []

        for bar in self.bars:
            if _kill_switch_enabled():
                logger.warning("Kill switch enabled; stopping backtest early.")
                risk_decisions.append(
                    {
                        "timestamp": _iso_ts(getattr(bar, "timestamp", None)),
                        "type": "kill_switch",
                        "reason": "enabled",
                    }
                )
                break

            symbol = (
                getattr(bar, "symbol", None)
                or getattr(self.config, "symbol", None)
                or "UNKNOWN"
            )
            close = float(getattr(bar, "close", 0.0))
            ts = getattr(bar, "timestamp", None)

            # Update trader market data (Trader expects a dict of prices)
            try:
                self.trader.update_market({symbol: close})
            except Exception:
                logger.exception("Trader.update_market failed")

            # Strategy -> candidate orders
            try:
                orders_iter = self.strategy(bar, self.trader)
                candidate_orders = list(orders_iter) if orders_iter is not None else []
            except Exception:
                logger.exception("Strategy failed; skipping orders for bar")
                candidate_orders = []

            # Risk filtering (optional)
            safe_orders = candidate_orders
            if self.risk_manager is not None and candidate_orders:
                safe_orders, decision = self._apply_risk(bar, candidate_orders)
                if decision is not None:
                    risk_decisions.append(decision)

            # Execute orders
            if safe_orders:
                try:
                    exec_result = self.trader.process_orders(safe_orders)
                    fills = _extract_fills(exec_result)
                    for fill in fills:
                        if isinstance(fill, dict):
                            fill = dict(fill)
                            fill.setdefault("timestamp", _iso_ts(ts))
                            trade_history.append(fill)
                except Exception:
                    logger.exception("Trader.process_orders failed")

            # Snapshot EVERY bar with required fields
            snap = self._portfolio_snapshot({symbol: close}, timestamp=ts)
            portfolio_history.append(snap)

        # Final snapshot (use last close if available)
        final_prices: Dict[str, float] = {}
        final_ts: Optional[Any] = None
        if self.bars:
            last = self.bars[-1]
            sym = (
                getattr(last, "symbol", None)
                or getattr(self.config, "symbol", None)
                or "UNKNOWN"
            )
            final_prices[sym] = float(getattr(last, "close", 0.0))
            final_ts = getattr(last, "timestamp", None)

        final_portfolio = self._portfolio_snapshot(final_prices, timestamp=final_ts)

        return BacktestResult(
            portfolio_history=portfolio_history,
            trade_history=trade_history,
            final_portfolio=final_portfolio,
            risk_decisions=risk_decisions,
        )

    def _apply_risk(self, bar: Bar, orders: List[Any]):
        """
        Supports multiple risk-manager APIs:

        - evaluate_orders(bar, orders) -> {"approved_orders": [...], ...} OR object.approved_orders
        - filter_orders(bar, orders) -> filtered_orders
        - filter_orders(orders) -> filtered_orders
        """
        rm = self.risk_manager

        fn = getattr(rm, "evaluate_orders", None)
        if callable(fn):
            try:
                decision = fn(bar, orders)
                approved = _get_attr_or_key(decision, "approved_orders")
                if approved is None:
                    approved = _get_attr_or_key(decision, "orders")
                safe = list(approved) if approved is not None else []
                return safe, _normalize_decision(decision, bar)
            except Exception:
                logger.exception("risk_manager.evaluate_orders failed")
                return orders, None

        fn = getattr(rm, "filter_orders", None)
        if callable(fn):
            try:
                try:
                    safe = fn(bar, orders)
                except TypeError:
                    safe = fn(orders)
                return list(safe) if safe is not None else [], None
            except Exception:
                logger.exception("risk_manager.filter_orders failed")
                return orders, None

        return orders, None

    def _portfolio_snapshot(
        self, prices: Dict[str, float], timestamp: Optional[Any]
    ) -> Dict[str, Any]:
        ts_iso = _iso_ts(timestamp)

        portfolio = getattr(self.trader, "portfolio", None)
        snap: Dict[str, Any] = {}

        if portfolio is not None:
            snap_fn = getattr(portfolio, "snapshot", None)
            if callable(snap_fn):
                try:
                    snap_any = snap_fn(prices)
                except TypeError:
                    snap_any = snap_fn()
                except Exception:
                    logger.exception("Portfolio.snapshot() failed")
                    snap_any = None

                if isinstance(snap_any, dict):
                    snap = dict(snap_any)
                elif snap_any is not None:
                    try:
                        snap = dict(snap_any)  # type: ignore[arg-type]
                    except Exception:
                        snap = {}

        if not snap:
            snap = self._snapshot_from_attrs(prices)

        # Required fields
        snap["timestamp"] = ts_iso
        if "equity" not in snap or snap.get("equity") is None:
            snap["equity"] = self._compute_equity(prices)

        return snap

    def _snapshot_from_attrs(self, prices: Dict[str, float]) -> Dict[str, Any]:
        portfolio = getattr(self.trader, "portfolio", None)

        cash = _safe_float(getattr(portfolio, "cash", None), default=0.0)
        positions_raw = getattr(portfolio, "positions", None)
        positions: Dict[str, float] = {}

        if isinstance(positions_raw, dict):
            for k, v in positions_raw.items():
                positions[str(k)] = _safe_float(v, default=0.0)

        equity = cash + sum(
            qty * float(prices.get(sym, 0.0)) for sym, qty in positions.items()
        )
        return {"cash": cash, "positions": positions, "equity": float(equity)}

    def _compute_equity(self, prices: Dict[str, float]) -> float:
        portfolio = getattr(self.trader, "portfolio", None)
        if portfolio is None:
            return 0.0

        cash = _safe_float(getattr(portfolio, "cash", None), default=0.0)
        positions_raw = getattr(portfolio, "positions", None)

        total = cash
        if isinstance(positions_raw, dict):
            for sym, qty in positions_raw.items():
                total += _safe_float(qty, 0.0) * float(prices.get(str(sym), 0.0))
        return float(total)


def _iso_ts(ts: Optional[Any]) -> str:
    if ts is None:
        return datetime.utcnow().isoformat()
    if isinstance(ts, str):
        return ts
    if hasattr(ts, "isoformat"):
        try:
            return ts.isoformat()
        except Exception:
            pass
    return str(ts)


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _get_attr_or_key(obj: Any, name: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def _normalize_decision(decision: Any, bar: Bar) -> Dict[str, Any]:
    out: Dict[str, Any] = {"timestamp": _iso_ts(getattr(bar, "timestamp", None))}
    if isinstance(decision, dict):
        out.update(decision)
    else:
        for k in ("reason", "approved_orders", "rejected_orders", "details"):
            v = getattr(decision, k, None)
            if v is not None:
                out[k] = v
    return out


def _extract_fills(exec_result: Any) -> List[Dict[str, Any]]:
    """
    Normalize different trader.process_orders return shapes.

    Supported:
      - {"fills": [ {...}, ... ]}
      - {"trades": [ {...}, ... ]}
      - list[dict]
    """
    if exec_result is None:
        return []
    if isinstance(exec_result, list):
        return [x for x in exec_result if isinstance(x, dict)]
    if isinstance(exec_result, dict):
        fills = exec_result.get("fills") or exec_result.get("trades") or []
        if isinstance(fills, list):
            return [x for x in fills if isinstance(x, dict)]
    return []
