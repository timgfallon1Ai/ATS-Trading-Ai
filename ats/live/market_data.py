from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, Optional, Protocol, Sequence

import requests

from ats.live.types import Bar

log = logging.getLogger("ats.live.market_data")


class MarketData(Protocol):
    def get_bars(self, symbols: Sequence[str]) -> Dict[str, Bar]:
        raise NotImplementedError

    def close(self) -> None:
        return


class MockMarketData:
    def __init__(self, prices: Dict[str, float]) -> None:
        self._prices: Dict[str, float] = {
            k.upper(): float(v) for k, v in prices.items()
        }
        self._tick: int = 0

    def get_bars(self, symbols: Sequence[str]) -> Dict[str, Bar]:
        self._tick += 1
        ts = datetime.utcnow()
        out: Dict[str, Bar] = {}
        for s in symbols:
            sym = str(s).upper()
            px = float(self._prices[sym])
            out[sym] = Bar(
                symbol=sym,
                timestamp=ts,
                open=px,
                high=px,
                low=px,
                close=px,
                volume=0.0,
                vwap=None,
                extra={"mock_tick": self._tick},
            )
        return out


class PolygonMarketData:
    """Polygon snapshot poller (REST).

    Uses: /v2/snapshot/locale/us/markets/stocks/tickers/{ticker}

    This returns a daily bar + last trade/quote. We treat lastTrade.p as "close".
    """

    def __init__(self, api_key: str, timeout_s: float = 10.0) -> None:
        if not api_key:
            raise ValueError("POLYGON_API_KEY is required for market_data=polygon")
        self._api_key = api_key
        self._timeout_s = float(timeout_s)
        self._session = requests.Session()

    def _fetch_one(self, symbol: str) -> Bar:
        sym = symbol.upper()
        url = (
            f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/{sym}"
        )
        resp = self._session.get(
            url, params={"apiKey": self._api_key}, timeout=self._timeout_s
        )
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results") or {}
        day = results.get("day") or {}
        last_trade = results.get("lastTrade") or {}

        # Best-effort parsing:
        o = float(day.get("o") or 0.0)
        h = float(day.get("h") or 0.0)
        low = float(day.get("l") or 0.0)
        v = float(day.get("v") or 0.0)
        vw = day.get("vw")

        last_price = last_trade.get("p")
        if last_price is None:
            last_price = day.get("c")
        if last_price is None:
            raise RuntimeError(f"Polygon snapshot missing price for {sym}")

        close = float(last_price)

        # Timestamp: if Polygon provides lastTrade.t, it's typically ms since epoch.
        ts_val = last_trade.get("t")
        ts = datetime.utcnow()
        if ts_val is not None:
            try:
                ts = datetime.utcfromtimestamp(float(ts_val) / 1000.0)
            except Exception:
                ts = datetime.utcnow()

        # If day fields are missing, fall back to close.
        if o <= 0:
            o = close
        if h <= 0:
            h = close
        if low <= 0:
            low = close

        return Bar(
            symbol=sym,
            timestamp=ts,
            open=o,
            high=h,
            low=low,
            close=close,
            volume=v,
            vwap=float(vw) if vw is not None else None,
            extra={"polygon_ticker": data.get("ticker")},
        )

    def get_bars(self, symbols: Sequence[str]) -> Dict[str, Bar]:
        out: Dict[str, Bar] = {}
        for s in symbols:
            sym = str(s).upper()
            try:
                out[sym] = self._fetch_one(sym)
            except Exception as e:
                log.exception("Polygon fetch failed for %s: %s", sym, e)
                raise
        return out

    def close(self) -> None:
        try:
            self._session.close()
        except Exception:
            return
