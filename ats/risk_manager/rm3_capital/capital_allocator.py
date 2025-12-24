from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional

from ats.types import CapitalAllocPacket

from .concentration_limits import ConcentrationLimits
from .exposure_rules import ExposureRules


def _get_direction(packet: Any) -> float:
    """Best-effort signed direction for a packet.

    Supported packet shapes:
    - packet.direction: +1 / -1 (int/float)
    - packet.side: 'buy'/'sell' or 'long'/'short'
    - packet.is_short: bool
    - packet.weight: signed (if present and target_dollars missing, we'll use weight directly)
    """
    if hasattr(packet, "direction"):
        try:
            return 1.0 if float(getattr(packet, "direction")) >= 0.0 else -1.0
        except (TypeError, ValueError):
            pass

    side = getattr(packet, "side", None)
    if isinstance(side, str):
        s = side.strip().lower()
        if s in {"sell", "short", "-1"}:
            return -1.0
        if s in {"buy", "long", "1"}:
            return 1.0

    if bool(getattr(packet, "is_short", False)):
        return -1.0

    return 1.0


def _get_magnitude(packet: Any) -> float:
    """Best-effort magnitude for a packet.

    Supported packet shapes:
    - packet.target_dollars (preferred; should be non-negative)
    - packet.dollars / packet.notional
    - packet.weight (used only if target_dollars is absent)
    """
    for attr in ("target_dollars", "dollars", "notional"):
        if hasattr(packet, attr):
            try:
                return max(0.0, float(getattr(packet, attr)))
            except (TypeError, ValueError):
                return 0.0

    if hasattr(packet, "weight"):
        try:
            return abs(float(getattr(packet, "weight")))
        except (TypeError, ValueError):
            return 0.0

    return 0.0


@dataclass(frozen=True)
class CapitalAllocatorConfig:
    """Config for RM-3 capital allocation rules.

    All outputs from :meth:`CapitalAllocator.allocate` are **signed weights**.
    """

    max_gross_leverage: float = 2.0
    max_net_leverage: float = 1.0
    max_symbol_weight: float = 0.25

    max_strategy_fraction_of_gross: float = 0.60
    min_symbol_strategy_fraction: float = 0.05

    allow_short: bool = True
    min_abs_weight: float = 0.0

    normalize_to_unit_gross: bool = True
    max_symbols: int = 100

    extra: Dict[str, Any] = field(default_factory=dict)


class CapitalAllocator:
    """RM-3 CapitalAllocator.

    Input: iterable of CapitalAllocPacket (or compatible objects).
    Output: dict symbol -> signed weight (float).
    """

    def __init__(self, config: Optional[CapitalAllocatorConfig] = None) -> None:
        self.config = config or CapitalAllocatorConfig()

        self._concentration = ConcentrationLimits(
            max_strategy_fraction_of_gross=self.config.max_strategy_fraction_of_gross,
            min_symbol_strategy_fraction=self.config.min_symbol_strategy_fraction,
        )
        self._exposure = ExposureRules(
            allow_short=self.config.allow_short,
            max_symbol_weight=self.config.max_symbol_weight,
            max_gross_leverage=self.config.max_gross_leverage,
            max_net_leverage=self.config.max_net_leverage,
            min_abs_weight=self.config.min_abs_weight,
        )

    def allocate(self, packets: Iterable[CapitalAllocPacket]) -> Dict[str, float]:
        """Allocate signed weights from packets and apply RM-3 constraints."""
        raw: Dict[str, float] = {}
        packets_list = list(packets)

        for p in packets_list:
            sym = getattr(p, "symbol", None)
            if sym is None:
                continue
            sym = str(sym).upper().strip()
            if not sym:
                continue

            weight_attr = getattr(p, "weight", None)
            has_target = any(
                hasattr(p, a) for a in ("target_dollars", "dollars", "notional")
            )

            if (weight_attr is not None) and (not has_target):
                try:
                    signed = float(weight_attr)
                except (TypeError, ValueError):
                    signed = 0.0
            else:
                signed = _get_direction(p) * _get_magnitude(p)

            if signed == 0.0:
                continue

            raw[sym] = raw.get(sym, 0.0) + float(signed)

        if not raw:
            return {}

        if self.config.normalize_to_unit_gross:
            gross = sum(abs(v) for v in raw.values())
            if gross > 0.0:
                weights = {sym: val / gross for sym, val in raw.items()}
            else:
                weights = {}
        else:
            weights = dict(raw)

        if self.config.max_symbols and len(weights) > self.config.max_symbols:
            top = sorted(weights.items(), key=lambda kv: abs(kv[1]), reverse=True)[
                : self.config.max_symbols
            ]
            weights = dict(top)

        weights = self._concentration.apply(weights, packets_list)
        weights = self._exposure.apply(weights)

        return dict(sorted(weights.items(), key=lambda kv: kv[0]))

    def diagnostics(self, weights: Mapping[str, float]) -> Dict[str, float]:
        snap = self._exposure.snapshot(weights)
        return {
            "gross": float(snap.gross),
            "net": float(snap.net),
            "max_abs_symbol": float(snap.max_abs_symbol),
            "n_symbols": float(snap.n_symbols),
        }
