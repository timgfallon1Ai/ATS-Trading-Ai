# ats/backtester2/bt_validation.py

from __future__ import annotations

from ats.backtester2.bt_contracts import (
    CombinedSignal,
    FeatureSet,
    Fill,
    RawSignal,
    SizedOrder,
)


def validate_features(features: dict[str, FeatureSet]):
    if not isinstance(features, dict):
        raise ValueError("features must be dict[str, FeatureSet]")

    for sym, fset in features.items():
        if not isinstance(fset, FeatureSet):
            raise ValueError(f"FeatureSet for {sym} is not FeatureSet")
        if not isinstance(fset.values, dict):
            raise ValueError(f"FeatureSet.values for {sym} must be dict")
        for k, v in fset.values.items():
            if not isinstance(v, (int, float)):
                raise ValueError(f"Feature value {k} for {sym} is not numeric")


def validate_raw_signals(raw_signals: list[RawSignal]):
    for s in raw_signals:
        if not isinstance(s, RawSignal):
            raise ValueError("raw signal is not RawSignal")
        if not isinstance(s.direction, (int, float)):
            raise ValueError("signal.direction must be numeric")
        if not isinstance(s.strength, (int, float)):
            raise ValueError("signal.strength must be numeric")


def validate_combined_signals(combined: dict[str, CombinedSignal]):
    for sym, sig in combined.items():
        if not isinstance(sig, CombinedSignal):
            raise ValueError(f"combined[{sym}] is not CombinedSignal")
        if not isinstance(sig.target_weight, float):
            raise ValueError(f"combined[{sym}].target_weight must be float")


def validate_sized_orders(orders: list[SizedOrder]):
    for o in orders:
        if not isinstance(o, SizedOrder):
            raise ValueError("Not a SizedOrder")
        if not isinstance(o.size, (int, float)):
            raise ValueError("Order.size must be numeric")
        if not isinstance(o.notional, (int, float)):
            raise ValueError("Order.notional must be numeric")


def validate_fills(fills: list[Fill]):
    for f in fills:
        if not isinstance(f, Fill):
            raise ValueError("Not a Fill")
        if not isinstance(f.qty, (int, float)):
            raise ValueError("Fill.qty must be numeric")
        if not isinstance(f.price, (int, float)):
            raise ValueError("Fill.price must be numeric")
        if not isinstance(f.timestamp, int):
            raise ValueError("Fill.timestamp must be int")


def validate_positions(positions: dict[str, float]):
    for sym, qty in positions.items():
        if not isinstance(qty, (int, float)):
            raise ValueError(f"Position {sym} qty must be numeric")
