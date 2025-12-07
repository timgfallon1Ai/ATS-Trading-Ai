# ats/backtester2/core/timeline.py

from __future__ import annotations

from typing import Iterator, List

from .bar import Bar


class Timeline:
    """A deterministic wrapper around a list of UBF bars.
    Used by BacktestEngine for controlled iteration.

    - next_bar() returns the next bar.
    - at_end() indicates whether iteration is finished.
    - reset() moves the timeline back to the first bar.
    """

    def __init__(self, bars: List[Bar]):
        self._bars: List[Bar] = bars
        self._index: int = 0
        self._length: int = len(bars)

    def reset(self) -> None:
        self._index = 0

    def next_bar(self) -> Bar | None:
        if self._index >= self._length:
            return None
        bar = self._bars[self._index]
        self._index += 1
        return bar

    def at_end(self) -> bool:
        return self._index >= self._length

    def __iter__(self) -> Iterator[Bar]:
        for bar in self._bars:
            yield bar
