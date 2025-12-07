from typing import List

from .schema import Bar, UBFSchema


def validate_bars(raw_bars: List[dict]) -> List[Bar]:
    """Convert + validate a list of raw dicts into typed UBF Bar objects."""
    bars: List[Bar] = []

    for raw in raw_bars:
        bar = UBFSchema.to_bar(raw)
        bars.append(bar)

    return bars
