from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from .broker import BrokerState
from .types import OrderFill, OrderRequest


@dataclass
class IBKRBroker:
    """Interactive Brokers broker adapter via ib_insync.

    Phase 15.1 notes:
    - This is intentionally minimal and intended for paper trading first.
    - You must have TWS or IB Gateway running and API enabled.
    - Dependency is optional: `pip install ib-insync`.

    Environment variables (defaults shown):
    - IBKR_HOST=127.0.0.1
    - IBKR_PORT=7497 (paper) / 7496 (live)  (your setup may differ)
    - IBKR_CLIENT_ID=1
    - IBKR_ACCOUNT (optional; used for better account summary filtering)

    Safety:
    - The Live runner requires explicit `--execute` to place orders.
    - For non-paper trading you should also gate with an additional allow-live flag in your own ops.
    """

    host: str = "127.0.0.1"
    port: int = 7497
    client_id: int = 1
    account: Optional[str] = None
    name: str = "ibkr"

    _ib: object = field(default=None, init=False)

    def connect(self) -> None:
        try:
            from ib_insync import IB  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "ib_insync is not installed. Install it with: pip install ib-insync"
            ) from e

        ib = IB()
        ib.connect(self.host, int(self.port), clientId=int(self.client_id))
        self._ib = ib

    def get_state(self) -> BrokerState:
        if self._ib is None:
            self.connect()

        ib = self._ib

        cash = 0.0
        try:
            summary = (
                ib.accountSummary(account=self.account)
                if self.account
                else ib.accountSummary()
            )
            # accountSummary returns list of TagValue: (account, tag, value, currency)
            for tv in summary:
                if getattr(tv, "currency", None) not in (None, "", "USD"):
                    continue
                if tv.tag in ("AvailableFunds", "TotalCashValue", "CashBalance"):
                    try:
                        cash = float(tv.value)
                        break
                    except Exception:
                        continue
        except Exception:
            cash = 0.0

        positions: Dict[str, float] = {}
        try:
            for p in ib.positions():
                sym = getattr(p.contract, "symbol", None)
                qty = float(p.position)
                if sym:
                    positions[sym] = positions.get(sym, 0.0) + qty
        except Exception:
            positions = {}

        return BrokerState(cash=cash, positions=positions)

    def place_order(
        self, order: OrderRequest, price: float, timestamp: datetime
    ) -> OrderFill:
        if self._ib is None:
            self.connect()

        try:
            from ib_insync import MarketOrder, Stock  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "ib_insync is not installed. Install it with: pip install ib-insync"
            ) from e

        ib = self._ib
        action = "BUY" if order.side == "buy" else "SELL"

        contract = Stock(order.symbol, "SMART", "USD")

        qty = int(order.quantity)
        if qty <= 0:
            raise ValueError(f"IBKR quantity must be >= 1 share; got {order.quantity}")

        ib_order = MarketOrder(action, qty)
        trade = ib.placeOrder(contract, ib_order)

        raw = {}
        try:
            raw = {
                "permId": getattr(trade.order, "permId", None),
                "orderId": getattr(trade.order, "orderId", None),
                "status": getattr(trade.orderStatus, "status", None),
            }
        except Exception:
            raw = {}

        return OrderFill(
            order_id=str(raw.get("orderId") or uuid4()),
            symbol=order.symbol,
            side=order.side,
            quantity=float(qty),
            price=float(price),
            timestamp=timestamp,
            broker=self.name,
            raw=raw,
        )

    def flatten_all(
        self, prices: Dict[str, float], timestamp: datetime
    ) -> List[OrderFill]:
        fills: List[OrderFill] = []
        state = self.get_state()
        for symbol, qty in state.positions.items():
            px = float(prices.get(symbol, 0.0))
            if px <= 0:
                continue
            side = "sell" if qty > 0 else "buy"
            fills.append(
                self.place_order(
                    OrderRequest(
                        symbol=symbol,
                        side=side,
                        quantity=abs(qty),
                        tag="kill_switch_flatten",
                    ),
                    price=px,
                    timestamp=timestamp,
                )
            )
        return fills

    def close(self) -> None:
        if self._ib is not None:
            try:
                self._ib.disconnect()
            except Exception:
                pass
            self._ib = None
