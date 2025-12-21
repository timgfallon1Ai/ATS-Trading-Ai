cat > ats / backtester2 / ensemble_strategy.py << "EOF"
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
    """
    AnalystEngine -> Aggregator -> (optional RM3 weights) -> Orders.

    max_position_frac is applied to the capital base used for sizing.
    """

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
    positions = snap.get("positions")
    if isinstance(positions, dict):
        pos = positions.get(symbol)
        if isinstance(pos, dict) and "quantity" in pos:
            return _safe_float(pos.get("quantity"), 0.0)

    portfolio = getattr(trader, "portfolio", None)
    if portfolio is not None:
        pmap = getattr(portfolio, "positions", None)
        if isinstance(pmap, dict) and symbol in pmap:
            p = pmap[symbol]
            return _safe_float(getattr(p, "quantity", 0.0), 0.0)

    return 0.0


class EnsembleStrategy:
    """
    Callable strategy for BacktestEngine.

    Maintains a rolling history DataFrame (OHLCV) and generates
    market orders toward a target position derived from:
      - AnalystEngine aggregated score/confidence
      - Aggregator direction mapping
      - optional RiskManager.run_allocation_batch weights
    """

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

        # Debug/telemetry
        self.last_allocation: Optional[Dict[str, Any]] = None
        self.last_signal: Optional[Dict[str, Any]] = None
        self.last_signed_weight: float = 0.0

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
                normalized_allocations,
                base_capital=base_capital,
            )
            if isinstance(weights, dict):
                w = _safe_float(weights.get(self.symbol, 1.0), 1.0)
                return max(0.0, min(1.0, abs(w)))
        except Exception:
            pass

        return 1.0

    def __call__(self, bar: Bar, trader: Any) -> Sequence[Order]:
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

        if isinstance(alloc_obj, dict):
            alloc: Dict[str, Any] = dict(alloc_obj)
        else:
            alloc = dict(getattr(alloc_obj, "__dict__", {}))

        batch = self.aggregator.prepare_batch([alloc])
        combined_signals = batch.get("combined_signals") or []
        normalized_allocs = batch.get("allocations") or []

        signal: Dict[str, Any] = combined_signals[0] if combined_signals else {}
        direction = str(signal.get("direction", "flat"))
        score = _safe_float(signal.get("score", alloc.get("score", 0.0)), 0.0)
        confidence = _safe_float(
            signal.get("confidence", alloc.get("confidence", 0.0)), 0.0
        )

        if not self.config.allow_short and direction == "short":
            direction = "flat"

        if direction == "long":
            sign = 1.0
        elif direction == "short":
            sign = -1.0
        else:
            sign = 0.0

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

        self.last_allocation = alloc
        self.last_signal = dict(signal)
        self.last_signed_weight = signed_weight

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


EOF
