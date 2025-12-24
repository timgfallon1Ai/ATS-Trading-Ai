from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Tuple


def _get_strategy_breakdown(packet: Any) -> Dict[str, float]:
    """Best-effort extraction of per-strategy contribution for a packet.

    Supported shapes (to stay compatible as packet schemas evolve):
    - packet.strategy_breakdown (dict[str, float])
    - packet.metadata["strategy_breakdown"] (dict[str, float])
    - packet.meta["strategy_breakdown"] (dict[str, float])

    Values may be any real numbers; we convert to floats and later use absolute values.
    """
    bd = getattr(packet, "strategy_breakdown", None)
    if isinstance(bd, dict):
        return {str(k): float(v) for k, v in bd.items()}

    for meta_attr in ("metadata", "meta"):
        meta = getattr(packet, meta_attr, None)
        if isinstance(meta, dict):
            bd2 = meta.get("strategy_breakdown")
            if isinstance(bd2, dict):
                return {str(k): float(v) for k, v in bd2.items()}

    return {}


def _normalize_abs(breakdown: Mapping[str, float]) -> Dict[str, float]:
    total = sum(abs(v) for v in breakdown.values())
    if total <= 0.0:
        return {}
    return {k: abs(v) / total for k, v in breakdown.items() if v != 0.0}


@dataclass(frozen=True)
class StrategyConcentrationSnapshot:
    """Telemetry: how much gross weight is attributed to each strategy."""

    gross: float
    by_strategy: Dict[str, float]


class ConcentrationLimits:
    """RM-3 Concentration Limits.

    Soft limiter: scales symbol weights when one strategy dominates gross exposure.
    It does NOT re-rank strategies or change selection logic.
    """

    def __init__(
        self,
        *,
        max_strategy_fraction_of_gross: float = 0.60,
        min_symbol_strategy_fraction: float = 0.05,
    ) -> None:
        if not (0.0 < max_strategy_fraction_of_gross <= 1.0):
            raise ValueError("max_strategy_fraction_of_gross must be in (0, 1]")
        if not (0.0 <= min_symbol_strategy_fraction <= 1.0):
            raise ValueError("min_symbol_strategy_fraction must be in [0, 1]")

        self.max_strategy_fraction_of_gross = float(max_strategy_fraction_of_gross)
        self.min_symbol_strategy_fraction = float(min_symbol_strategy_fraction)

    @staticmethod
    def snapshot(
        weights: Mapping[str, float], packets: Iterable[Any]
    ) -> StrategyConcentrationSnapshot:
        w = {str(k): float(v) for k, v in weights.items()}
        gross = sum(abs(v) for v in w.values())
        by_strategy: Dict[str, float] = {}

        if gross <= 0.0:
            return StrategyConcentrationSnapshot(gross=0.0, by_strategy={})

        for p in packets:
            sym = getattr(p, "symbol", None)
            if sym is None:
                continue
            sym = str(sym)
            if sym not in w:
                continue

            fracs = _normalize_abs(_get_strategy_breakdown(p))
            if not fracs:
                continue

            sym_abs = abs(w[sym])
            for strat, frac in fracs.items():
                by_strategy[strat] = by_strategy.get(strat, 0.0) + (sym_abs * frac)

        return StrategyConcentrationSnapshot(
            gross=float(gross), by_strategy=by_strategy
        )

    def apply(
        self, weights: Mapping[str, float], packets: Iterable[Any]
    ) -> Dict[str, float]:
        """Scale down symbols so no single strategy dominates gross exposure."""
        w: Dict[str, float] = {str(k): float(v) for k, v in weights.items()}
        gross = sum(abs(v) for v in w.values())
        if gross <= 0.0:
            return {}

        cap = self.max_strategy_fraction_of_gross * gross

        strat_exposure: Dict[str, float] = {}
        sym_strat_frac: Dict[Tuple[str, str], float] = {}

        for p in packets:
            sym = getattr(p, "symbol", None)
            if sym is None:
                continue
            sym = str(sym)
            if sym not in w:
                continue

            fracs = _normalize_abs(_get_strategy_breakdown(p))
            if not fracs:
                continue

            sym_abs = abs(w[sym])
            for strat, frac in fracs.items():
                sym_strat_frac[(sym, strat)] = frac
                strat_exposure[strat] = strat_exposure.get(strat, 0.0) + (
                    sym_abs * frac
                )

        # If we have no strategy info, do nothing.
        if not strat_exposure:
            return w

        breached = {s: exp for s, exp in strat_exposure.items() if exp > cap}
        if not breached:
            return w

        symbol_scale: Dict[str, float] = {sym: 1.0 for sym in w.keys()}

        for strat, exp in breached.items():
            scale = cap / exp  # < 1.0
            for (sym, s), frac in sym_strat_frac.items():
                if s != strat:
                    continue
                if frac < self.min_symbol_strategy_fraction:
                    continue
                symbol_scale[sym] = min(symbol_scale.get(sym, 1.0), scale)

        adjusted: Dict[str, float] = {}
        for sym, val in w.items():
            sc = symbol_scale.get(sym, 1.0)
            new_val = val * sc
            if new_val != 0.0:
                adjusted[sym] = new_val

        return adjusted

    def apply_with_snapshot(
        self, weights: Mapping[str, float], packets: Iterable[Any]
    ) -> Tuple[Dict[str, float], StrategyConcentrationSnapshot]:
        adjusted = self.apply(weights, packets)
        return adjusted, self.snapshot(adjusted, packets)
