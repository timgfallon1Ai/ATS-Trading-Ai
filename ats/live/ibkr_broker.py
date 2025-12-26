from __future__ import annotations

import logging
from typing import Dict, Optional, Sequence

from ats.live.broker import Broker
from ats.trader.order import Order

log = logging.getLogger("ats.live.ibkr_broker")


class IBKRBroker(Broker):
    """IBKR broker adapter (lazy-imports ib_insync).

    NOTE: This is intentionally minimal for Phase 15.
    - Requires TWS or IB Gateway running
    - Your CLI safety gate must be used: --execute requires --allow-live
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7497,
        client_id: int = 7,
    ) -> None:
        try:
            from ib_insync import IB  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "ib_insync is not installed. Run: pip install ib-insync"
            ) from e

        self._ib = IB()
        self._ib.connect(host, int(port), clientId=int(client_id))
        log.info(
            "Connected to IBKR host=%s port=%s client_id=%s", host, port, client_id
        )

    def get_positions(self) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for p in self._ib.positions():
            sym = getattr(p.contract, "symbol", None)
            if not sym:
                continue
            out[str(sym).upper()] = float(p.position)
        return out

    def place_order(self, order: Order, price: Optional[float] = None) -> None:
        # price is ignored for IBKR (market orders)
        try:
            from ib_insync import MarketOrder, Stock  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError("ib_insync is not available") from e

        sym = str(order.symbol).upper()
        qty = float(order.size)
        if qty <= 0:
            return

        side = str(order.side).lower()
        action = "BUY" if side == "buy" else "SELL" if side == "sell" else None
        if action is None:
            raise ValueError(f"Unknown side: {order.side}")

        contract = Stock(sym, "SMART", "USD")
        self._ib.qualifyContracts(contract)
        ib_order = MarketOrder(action, qty)

        trade = self._ib.placeOrder(contract, ib_order)
        log.info(
            "IBKR ORDER %s %s qty=%.6f status=%s",
            action,
            sym,
            qty,
            trade.orderStatus.status,
        )

    def flatten(
        self,
        prices: Dict[str, float],
        symbols: Optional[Sequence[str]] = None,
    ) -> None:
        positions = self.get_positions()
        universe = [s.upper() for s in symbols] if symbols else list(positions.keys())
        for sym in universe:
            qty = float(positions.get(sym, 0.0))
            if abs(qty) < 1e-12:
                continue
            if qty > 0:
                self.place_order(
                    Order(symbol=sym, side="sell", size=abs(qty), order_type="market")
                )
            else:
                self.place_order(
                    Order(symbol=sym, side="buy", size=abs(qty), order_type="market")
                )

    def close(self) -> None:
        try:
            self._ib.disconnect()
        except Exception:
            return
