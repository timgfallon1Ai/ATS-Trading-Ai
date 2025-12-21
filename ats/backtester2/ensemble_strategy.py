from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

import pandas as pd

from ats.aggregator.aggregator import Aggregator, AggregatorConfig
from ats.analyst.analyst_engine import AnalystEngine
from ats.analyst.registry import make_strategies
from ats.trader.order_types import Order

from .types import Bar


@dataclass(frozen=True)
class EnsembleStrategyConfig:
    strategy_names: Optional[Sequence[str]] = None
    max_position_frac: float = 0.20
    min_trade_qty: float = 1.0
    round_lot: float = 1.0
    allow_short: bool = True
    use_risk_weights: bool = True
    meta_source: str = "ensemble"


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def _to_pd_timestamp(value: Any) -> pd.Timestamp:
    try:
        return pd.Timestamp(value)
    except Exception:
        return pd.Timestamp.utcnow()


def _portfolio_snapshot(trader: Any, prices: Dict[str, float]) -> Dict[str, Any]:
    portfolio = getattr(trader, "portfolio", None)
    if portfolio is not None and hasattr(portfolio, "snapshot"):
        try:
            snap = portfolio.snapshot(prices)
            if isinstance(snap, dict):
                return snap
        except Exception:
            pass
    return {"equity": 0.0, "positions": {}}


def _current_qty(trader: Any, snap: Dict[str, Any], symbol: str) -> float:
    """
    Source of truth order:
      1) Trader.portfolio.positions (object model)
      2) snapshot["positions"][symbol]["quantity"] (dict model)
    """
    sym_keys = [symbol, str(symbol).upper(), str(symbol).lower()]

    portfolio = getattr(trader, "portfolio", None)
    if portfolio is not None:
        # Common convenience method
        if hasattr(portfolio, "position_qty"):
            for s in sym_keys:
                try:
                    return _safe_float(portfolio.position_qty(s), 0.0)
                except Exception:
                    pass

        positions_obj = getattr(portfolio, "positions", None)
        if isinstance(positions_obj, dict):
            for s in sym_keys:
                if s in positions_obj:
                    pos = positions_obj[s]
                    if isinstance(pos, dict):
                        return _safe_float(pos.get("quantity"), 0.0)
                    return _safe_float(getattr(pos, "quantity", 0.0), 0.0)

    positions = snap.get("positions")
    if isinstance(positions, dict):
        for s in sym_keys:
            pos = positions.get(s)
            if isinstance(pos, dict) and "quantity" in pos:
                return _safe_float(pos.get("quantity"), 0.0)

    return 0.0


class EnsembleStrategy:
    def __init__(
        self,
        symbol: str,
        risk_manager: Any = None,
        config: EnsembleStrategyConfig = EnsembleStrategyConfig(),
    ) -> None:
        self.symbol = symbol
        self.risk_manager = risk_manager
        self.config = config

        self.analyst = AnalystEngine(strategies=make_strategies(config.strategy_names))
        self.aggregator = Aggregator(config=AggregatorConfig())
        self._rows: List[Dict[str, Any]] = []

    def _history_df(self) -> pd.DataFrame:
        df = pd.DataFrame(self._rows)
        if df.empty:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        for c in ("open", "high", "low", "close", "volume"):
            if c not in df.columns:
                df[c] = 0.0
        return df

    def _capital_base_for_sizing(self, snap: Dict[str, Any]) -> float:
        equity = _safe_float(snap.get("equity"), 0.0)

        principal_floor = snap.get("principal_floor")
        if principal_floor is None:
            principal_floor = snap.get("starting_cash")
        if principal_floor is None:
            principal_floor = snap.get("starting_capital")
        if principal_floor is None:
            principal_floor = equity

        principal_floor_f = _safe_float(principal_floor, equity)

        pools = snap.get("pools")
        profit_equity = 0.0
        if isinstance(pools, dict):
            profit_equity = _safe_float(pools.get("profit_equity"), 0.0)

        aggressive_enabled = bool(snap.get("aggressive_enabled", False))
        base = (
            principal_floor_f + profit_equity
            if aggressive_enabled
            else principal_floor_f
        )
        if base <= 0.0:
            base = equity if equity > 0 else 1.0
        return base

    def _rm_weight_abs(
        self, normalized_allocations: List[Dict[str, Any]], base_capital: float
    ) -> float:
        if self.risk_manager is None or not self.config.use_risk_weights:
            return 1.0
        if not hasattr(self.risk_manager, "run_allocation_batch"):
            return 1.0
        try:
            weights = self.risk_manager.run_allocation_batch(
                normalized_allocations, base_capital=base_capital
            )
            if isinstance(weights, dict):
                w = _safe_float(weights.get(self.symbol, 1.0), 1.0)
                return max(0.0, min(1.0, abs(w)))
        except Exception:
            pass
        return 1.0

    def __call__(self, bar: Bar, trader: Any):
        self._rows.append(
            {
                "timestamp": bar.timestamp,
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": float(bar.close),
                "volume": float(getattr(bar, "volume", 0.0) or 0.0),
            }
        )

        df = self._history_df()
        ts = _to_pd_timestamp(bar.timestamp)

        alloc_obj = self.analyst.evaluate(self.symbol, df, ts)
        alloc: Dict[str, Any] = (
            dict(alloc_obj)
            if isinstance(alloc_obj, dict)
            else dict(getattr(alloc_obj, "__dict__", {}))
        )

        batch = self.aggregator.prepare_batch([alloc])
        combined_signals = batch.get("combined_signals") or []
        normalized_allocs = batch.get("allocations") or []

        signal = combined_signals[0] if combined_signals else {}
        direction = str(signal.get("direction", "flat"))
        score = _safe_float(signal.get("score", alloc.get("score", 0.0)), 0.0)
        confidence = _safe_float(
            signal.get("confidence", alloc.get("confidence", 0.0)), 0.0
        )

        if not self.config.allow_short and direction == "short":
            direction = "flat"

        sign = 1.0 if direction == "long" else (-1.0 if direction == "short" else 0.0)
        intensity = min(1.0, abs(score) * max(0.0, min(1.0, confidence)))

        price = float(bar.close)
        if price <= 0.0:
            return []

        snap = _portfolio_snapshot(trader, {self.symbol: price})
        base_capital = self._capital_base_for_sizing(snap)

        rm_w_abs = self._rm_weight_abs(list(normalized_allocs), base_capital)
        signed_weight = sign * rm_w_abs * intensity

        max_frac = max(0.0, float(self.config.max_position_frac))
        target_notional = signed_weight * base_capital * max_frac
        target_qty = target_notional / price

        lot = float(self.config.round_lot)
        if lot > 0:
            target_qty = round(target_qty / lot) * lot

        current_qty = _current_qty(trader, snap, self.symbol)
        delta_qty = target_qty - current_qty

        if abs(delta_qty) < float(self.config.min_trade_qty):
            return []

        side = "buy" if delta_qty > 0 else "sell"
        size = abs(delta_qty)

        return [
            Order(
                symbol=self.symbol,
                side=side,
                size=float(size),
                order_type="market",
                meta={
                    "source": self.config.meta_source,
                    "direction": direction,
                    "score": score,
                    "confidence": confidence,
                    "rm_weight_abs": rm_w_abs,
                    "signed_weight": signed_weight,
                    "target_qty": target_qty,
                    "current_qty": current_qty,
                },
            )
        ]
