# ats/backtester2/positions.py

from __future__ import annotations

from typing import Dict, List, Optional


class TradeRecord:
    """Single executed trade. Used for auditing, dashboarding, and RM feedback."""

    def __init__(
        self,
        symbol: str,
        side: str,
        qty: float,
        entry_price: float,
        exit_price: Optional[float] = None,
        pnl: Optional[float] = None,
        timestamp: Optional[int] = None,
    ):
        self.symbol = symbol
        self.side = side  # "LONG" | "SHORT"
        self.qty = qty
        self.entry_price = entry_price
        self.exit_price = exit_price
        self.pnl = pnl
        self.timestamp = timestamp  # integer offset bar index

    def close(self, exit_price: float):
        """Close an open trade and compute PnL."""
        self.exit_price = exit_price

        if self.side == "LONG":
            self.pnl = (exit_price - self.entry_price) * self.qty
        else:  # SHORT
            self.pnl = (self.entry_price - exit_price) * self.qty

        return self.pnl


class PositionsLedger:
    """Tracks open positions and closed trades across all symbols.
    No assumptions about portfolio construction—only stores results.

    The PortfolioSimulator handles:
        - sizing
        - fills
        - capital routing
        - RM constraints

    Ledger handles:
        - open/close trades
        - tracking lifecycle
        - producing a clean trade history for dashboards
    """

    def __init__(self):
        # Open positions keyed by symbol
        self.open_positions: Dict[str, TradeRecord] = {}

        # Chronological list of all closed trades
        self.closed_trades: List[TradeRecord] = []

    # -------------------------------------------------------
    # OPENING TRADES
    # -------------------------------------------------------
    def open_trade(
        self,
        symbol: str,
        side: str,
        qty: float,
        price: float,
        timestamp: int,
    ):
        """Opens a new position for the symbol.
        If there is an existing open position in that symbol, it will be forcibly closed.
        """
        # If a trade is already open, close it first.
        if symbol in self.open_positions:
            prev = self.open_positions[symbol]
            prev.close(price)
            self.closed_trades.append(prev)
            del self.open_positions[symbol]

        new_trade = TradeRecord(
            symbol=symbol,
            side=side,
            qty=qty,
            entry_price=price,
            timestamp=timestamp,
        )

        self.open_positions[symbol] = new_trade

    # -------------------------------------------------------
    # CLOSING TRADES
    # -------------------------------------------------------
    def close_trade(self, symbol: str, exit_price: float):
        """Close a trade for a symbol if it exists."""
        if symbol not in self.open_positions:
            return 0.0

        trade = self.open_positions[symbol]
        pnl = trade.close(exit_price)

        self.closed_trades.append(trade)
        del self.open_positions[symbol]
        return pnl

    # -------------------------------------------------------
    # UTILITIES
    # -------------------------------------------------------
    def close_all(self, price_map: Dict[str, float]):
        """Force-close all open trades at the final bar."""
        for symbol, trade in list(self.open_positions.items()):
            exit_price = price_map.get(symbol, trade.entry_price)
            trade.close(exit_price)
            self.closed_trades.append(trade)
            del self.open_positions[symbol]

    def current_exposure(self) -> Dict[str, float]:
        """Returns symbol → signed quantity.
        LONG positions are positive, SHORT positions negative.
        """
        out = {}
        for sym, trade in self.open_positions.items():
            qty = trade.qty if trade.side == "LONG" else -trade.qty
            out[sym] = qty
        return out

    def realized_pnl(self) -> float:
        return sum(t.pnl for t in self.closed_trades if t.pnl is not None)

    def unrealized_pnl(self, price_map: Dict[str, float]) -> float:
        total = 0.0
        for sym, trade in self.open_positions.items():
            px = price_map.get(sym)
            if px is None:
                continue
            if trade.side == "LONG":
                total += (px - trade.entry_price) * trade.qty
            else:
                total += (trade.entry_price - px) * trade.qty
        return total

    def dump_trade_history(self) -> List[Dict[str, float]]:
        """Dashboard-ready JSON-serializable trade history."""
        out = []
        for t in self.closed_trades:
            out.append(
                {
                    "symbol": t.symbol,
                    "side": t.side,
                    "qty": t.qty,
                    "entry_price": t.entry_price,
                    "exit_price": t.exit_price,
                    "pnl": t.pnl,
                    "timestamp": t.timestamp,
                }
            )
        return out
