# ats/backtester2/ledger.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class LedgerEntry:
    timestamp: int
    symbol: str
    qty: int
    price: float
    direction: str  # "buy" or "sell"


@dataclass
class EquityPoint:
    timestamp: int
    equity: float
    pnl_open: float
    pnl_closed: float


class Ledger:
    """Tracks:
    - Positions per symbol
    - Open PnL
    - Closed PnL
    - Equity Curve
    - Trade history
    """

    def __init__(self, starting_equity: float):
        self.starting_equity = starting_equity

        self.positions: Dict[str, int] = {}
        self.avg_price: Dict[str, float] = {}

        self.closed_pnl: float = 0.0
        self.open_pnl: float = 0.0

        self.trade_log: List[LedgerEntry] = []
        self.equity_curve: List[EquityPoint] = []

    # ------------------------------------------------------------
    #  RECORDING FILLS
    # ------------------------------------------------------------

    def record_fill(self, fill: Dict[str, float]):
        symbol = fill["symbol"]
        qty = int(fill["qty"])
        price = float(fill["price"])
        ts = int(fill["timestamp"])

        direction = "buy" if qty > 0 else "sell"

        # Log raw trade
        self.trade_log.append(
            LedgerEntry(
                timestamp=ts,
                symbol=symbol,
                qty=qty,
                price=price,
                direction=direction,
            )
        )

        # Update position
        prior_qty = self.positions.get(symbol, 0)
        new_qty = prior_qty + qty

        # If we flip direction, close PnL on overlapping shares
        if prior_qty != 0 and (prior_qty > 0 > new_qty or prior_qty < 0 < new_qty):
            # Full close
            pnl = prior_qty * (price - self.avg_price.get(symbol, price))
            self.closed_pnl += pnl
            self.positions[symbol] = 0
            self.avg_price[symbol] = 0.0
            return

        # If adding to existing, adjust average price
        if prior_qty * qty > 0:
            total_cost = prior_qty * self.avg_price.get(symbol, price) + qty * price
            self.avg_price[symbol] = total_cost / (prior_qty + qty)
        else:
            # Opening new position
            self.avg_price[symbol] = price

        self.positions[symbol] = new_qty

    # ------------------------------------------------------------
    #  MTM (Mark to Market)
    # ------------------------------------------------------------

    def update_mark_to_market(self, prices: Dict[str, float], timestamp: int):
        """Update open PnL & equity based on current market prices."""
        pnl_open = 0.0

        for sym, qty in self.positions.items():
            if qty == 0:
                continue

            cur_price = prices.get(sym)
            if cur_price is None:
                continue

            pnl_open += qty * (cur_price - self.avg_price.get(sym, cur_price))

        self.open_pnl = pnl_open

        equity = self.starting_equity + self.closed_pnl + self.open_pnl

        self.equity_curve.append(
            EquityPoint(
                timestamp=timestamp,
                equity=equity,
                pnl_open=self.open_pnl,
                pnl_closed=self.closed_pnl,
            )
        )
