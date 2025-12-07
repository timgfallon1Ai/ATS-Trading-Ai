from __future__ import annotations

from typing import List, Set


class SymbolSubscriptionManager:
    """Keeps track of which symbols need to be streamed
    and which provider is responsible.
    """

    def __init__(self) -> None:
        self._polygon_subs: Set[str] = set()
        self._benzinga_subs: Set[str] = set()
        self._twitter_subs: Set[str] = set()
        self._ibkr_subs: Set[str] = set()

    # ---------------------------
    # Polygon
    # ---------------------------
    def add_polygon(self, symbol: str) -> None:
        self._polygon_subs.add(symbol)

    def polygon_list(self) -> List[str]:
        return sorted(self._polygon_subs)

    # ---------------------------
    # Benzinga
    # ---------------------------
    def add_benzinga(self, symbol: str) -> None:
        self._benzinga_subs.add(symbol)

    def benzinga_list(self) -> List[str]:
        return sorted(self._benzinga_subs)

    # ---------------------------
    # Twitter
    # ---------------------------
    def add_twitter(self, symbol: str) -> None:
        self._twitter_subs.add(symbol)

    def twitter_list(self) -> List[str]:
        return sorted(self._twitter_subs)

    # ---------------------------
    # IBKR
    # ---------------------------
    def add_ibkr(self, symbol: str) -> None:
        self._ibkr_subs.add(symbol)

    def ibkr_list(self) -> List[str]:
        return sorted(self._ibkr_subs)
