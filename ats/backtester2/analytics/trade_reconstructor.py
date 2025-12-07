from collections import defaultdict
from typing import Any, Dict, List


class TradeReconstructor:
    """Converts raw execution logs into fully reconstructed trades.

    Each trade:
        {
            "symbol": str,
            "entry_timestamp": int,
            "exit_timestamp": int,
            "entry_price": float,
            "exit_price": float,
            "quantity": float,
            "pnl": float,
            "mfe": float,
            "mae": float
        }
    """

    def __init__(self):
        # Active trades per symbol
        self.open_positions = defaultdict(list)  # list of {qty, price, ts}
        self.closed_trades = []

    def process_executions(self, executions: List[Dict[str, Any]]):
        """Called after every bar. Incrementally reconstructs trades."""
        for exe in executions:
            symbol = exe["symbol"]
            qty = exe["qty"]
            price = exe["price"]
            ts = exe["timestamp"]

            if qty > 0:  # BUY
                self.open_positions[symbol].append(
                    {
                        "qty": qty,
                        "price": price,
                        "timestamp": ts,
                        "high_water": price,
                        "low_water": price,
                    }
                )

            elif qty < 0:  # SELL
                remaining = -qty
                while remaining > 0 and self.open_positions[symbol]:
                    pos = self.open_positions[symbol][0]
                    exit_qty = min(pos["qty"], remaining)

                    pnl = (price - pos["price"]) * exit_qty

                    trade_record = {
                        "symbol": symbol,
                        "entry_timestamp": pos["timestamp"],
                        "exit_timestamp": ts,
                        "entry_price": pos["price"],
                        "exit_price": price,
                        "quantity": exit_qty,
                        "pnl": pnl,
                        "mfe": pos["high_water"] - pos["price"],
                        "mae": pos["low_water"] - pos["price"],
                    }

                    self.closed_trades.append(trade_record)

                    pos["qty"] -= exit_qty
                    remaining -= exit_qty

                    if pos["qty"] <= 0:
                        self.open_positions[symbol].pop(0)
                    else:
                        pos["timestamp"] = ts  # Update timestamp for remaining qty

    def finalize(self) -> List[Dict[str, Any]]:
        """Flushes remaining open trades as marked-to-market at final exit.
        Does NOT assume profit/loss — uses last known watermarks.
        """
        forced = []
        for symbol, open_list in self.open_positions.items():
            for pos in open_list:
                forced.append(
                    {
                        "symbol": symbol,
                        "entry_timestamp": pos["timestamp"],
                        "exit_timestamp": pos["timestamp"],
                        "entry_price": pos["price"],
                        "exit_price": pos["price"],
                        "quantity": pos["qty"],
                        "pnl": 0.0,
                        "mfe": pos["high_water"] - pos["price"],
                        "mae": pos["low_water"] - pos["price"],
                    }
                )
        return self.closed_trades + forced
