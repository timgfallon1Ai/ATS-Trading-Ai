from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from ats.trader.order_types import Order
from ats.trader.trader import Trader

from .backtest_config import BacktestConfig
from .types import Bar

StrategyFn = Callable[[Bar, Trader], Sequence[Order]]


def _truthy(v: Optional[str]) -> bool:
    if v is None:
        return False
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}


def _kill_switch_paths() -> List[Path]:
    """
    The unit test sets ATS_KILL_SWITCH_FILE to a temp file.
    Historically, some implementations may also use logs/KILL_SWITCH.

    We check BOTH to be robust.
    """
    paths: List[Path] = []

    env_path = os.environ.get("ATS_KILL_SWITCH_FILE")
    if env_path:
        paths.append(Path(env_path))

    # Always include default
    paths.append(Path("logs") / "KILL_SWITCH")

    # de-dupe while preserving order
    seen: set[str] = set()
    out: List[Path] = []
    for p in paths:
        key = str(p)
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def _kill_switch_engaged() -> bool:
    """
    Engage when:
      - ATS_KILL_SWITCH_FORCE/ATS_KILL_SWITCH is truthy OR
      - ANY kill switch file exists (ATS_KILL_SWITCH_FILE and/or logs/KILL_SWITCH)

    We do NOT rely on ats.core.kill_switch internals here because the unit test
    is explicitly file/env based and we want the engine to pass even if the
    kill_switch module caches a path at import-time.
    """
    if _truthy(os.environ.get("ATS_KILL_SWITCH_FORCE")) or _truthy(
        os.environ.get("ATS_KILL_SWITCH")
    ):
        return True

    for p in _kill_switch_paths():
        try:
            if p.exists():
                return True
        except OSError:
            continue

    return False


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
    - Kill switch is checked at the START of every bar:
        - if engaged: emergency flatten, record snapshot, stop.
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

    def _build_flatten_orders(self, prices: Dict[str, float]) -> List[Order]:
        snap = self._portfolio_snapshot(prices)
        positions = snap.get("positions", {}) if isinstance(snap, dict) else {}
        orders: List[Order] = []

        if isinstance(positions, dict):
            for sym, pos in positions.items():
                if isinstance(pos, dict):
                    qty = float(pos.get("quantity", 0.0) or 0.0)
                else:
                    qty = float(getattr(pos, "quantity", 0.0) or 0.0)

                if abs(qty) < 1e-9:
                    continue

                side = "sell" if qty > 0 else "buy"
                orders.append(
                    Order(
                        symbol=str(sym),
                        side=side,
                        size=float(abs(qty)),
                        order_type="market",
                        meta={"source": "kill_switch", "reason": "emergency_flatten"},
                    )
                )

        return orders

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
        try:
            return self.trader.process_orders(
                orders, timestamp=getattr(bar, "timestamp", None)
            )
        except TypeError:
            return self.trader.process_orders(orders)

    def _record_result(
        self,
        result: Any,
        bar: Bar,
        prices: Dict[str, float],
        portfolio_history: List[Dict[str, Any]],
        trade_history: List[Dict[str, Any]],
        last_ledger_len: int,
    ) -> int:
        if isinstance(result, dict):
            port = result.get("portfolio")
            if isinstance(port, dict):
                port_entry = dict(port)
            else:
                port_entry = dict(self._portfolio_snapshot(prices))

            if "timestamp" not in port_entry:
                port_entry["timestamp"] = getattr(bar, "timestamp", None)
            portfolio_history.append(port_entry)

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

        port_entry = dict(self._portfolio_snapshot(prices))
        if "timestamp" not in port_entry:
            port_entry["timestamp"] = getattr(bar, "timestamp", None)
        portfolio_history.append(port_entry)
        return last_ledger_len

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
            prices = self._market_snapshot(bar)

            # Kill switch check BEFORE strategy on every bar.
            if _kill_switch_engaged():
                flatten_orders = self._build_flatten_orders(prices)
                result = self._process_orders(flatten_orders, bar)
                prices = self._market_snapshot(bar)
                last_ledger_len = self._record_result(
                    result,
                    bar,
                    prices,
                    portfolio_history,
                    trade_history,
                    last_ledger_len,
                )
                break

            candidate_orders = list(self.strategy(bar, self.trader))

            safe_orders, decision = self._evaluate_orders_with_risk(
                bar, candidate_orders
            )
            if decision is not None:
                risk_decisions.append(decision)

            result = self._process_orders(safe_orders, bar)
            prices = self._market_snapshot(bar)
            last_ledger_len = self._record_result(
                result, bar, prices, portfolio_history, trade_history, last_ledger_len
            )

        final_portfolio = portfolio_history[-1] if portfolio_history else None

        return BacktestResult(
            config=self.config,
            portfolio_history=portfolio_history,
            trade_history=trade_history,
            final_portfolio=final_portfolio,
            risk_decisions=risk_decisions,
        )
