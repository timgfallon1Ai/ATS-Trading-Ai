from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Mapping, Optional

from .fill_types import Fill


@dataclass
class Position:
    """Signed position. Positive = long, Negative = short."""

    quantity: float = 0.0
    avg_price: float = 0.0
    mark_price: float = 0.0

    def market_value(self) -> float:
        return float(self.quantity) * float(self.mark_price)

    def unrealized_pnl(self) -> float:
        # Works for both long and short because quantity is signed.
        return (float(self.mark_price) - float(self.avg_price)) * float(self.quantity)


@dataclass
class Portfolio:
    """
    Profit-focused portfolio with principal floor + profit pool.

    Key ideas:
      - principal_floor: your protected capital baseline (default = starting_cash)
      - equity = cash + net_exposure
      - profit_equity = max(0, equity - principal_floor)
      - aggressive_enabled turns on once profit_equity >= aggressive_profit_threshold
      - halted becomes True if equity falls below principal_floor (breach)

    Notes:
      - This Portfolio supports long and short positions.
      - Fees are supported via optional `fill.fee` (if present); execution engine may omit.
    """

    starting_cash: float = 100_000.0

    aggressive_profit_threshold: float = 1_000.0
    floor_breach_tolerance: float = 1e-6

    cash: float = field(init=False)
    principal_floor: float = field(init=False)

    realized_pnl: float = field(default=0.0, init=False)
    fees_paid: float = field(default=0.0, init=False)

    positions: Dict[str, Position] = field(default_factory=dict, init=False)

    aggressive_enabled: bool = field(default=False, init=False)
    halted: bool = field(default=False, init=False)
    halted_reason: Optional[str] = field(default=None, init=False)

    def __post_init__(self) -> None:
        self.cash = float(self.starting_cash)
        self.principal_floor = float(self.starting_cash)

    # ---------------------------------------------------------------------
    # Position helpers
    # ---------------------------------------------------------------------
    def _pos(self, symbol: str) -> Position:
        if symbol not in self.positions:
            self.positions[symbol] = Position()
        return self.positions[symbol]

    def mark_to_market(self, prices: Mapping[str, float]) -> None:
        """Update mark prices from a {symbol: price} map."""
        for sym, px in prices.items():
            if sym in self.positions:
                self.positions[sym].mark_price = float(px)

    # ---------------------------------------------------------------------
    # Core math
    # ---------------------------------------------------------------------
    def net_exposure(self) -> float:
        return sum(p.market_value() for p in self.positions.values())

    def gross_exposure(self) -> float:
        return sum(
            abs(float(p.quantity)) * float(p.mark_price)
            for p in self.positions.values()
        )

    def unrealized_pnl(self) -> float:
        return sum(p.unrealized_pnl() for p in self.positions.values())

    def equity(self) -> float:
        return float(self.cash) + float(self.net_exposure())

    def _recompute_pools_and_flags(self) -> None:
        eq = self.equity()

        profit_equity = max(0.0, eq - float(self.principal_floor))
        self.aggressive_enabled = profit_equity >= float(
            self.aggressive_profit_threshold
        )

        # Halt if we breach principal floor beyond tolerance.
        if eq < float(self.principal_floor) - float(self.floor_breach_tolerance):
            self.halted = True
            self.halted_reason = f"principal_floor_breach equity={eq:.6f} < floor={self.principal_floor:.6f}"
            # If principal is breached, aggressive must be disabled.
            self.aggressive_enabled = False
        else:
            self.halted = False
            self.halted_reason = None

    def pools(self) -> Dict[str, float]:
        """Return principal/profit pools based on current equity."""
        eq = self.equity()
        principal_equity = min(eq, float(self.principal_floor))
        profit_equity = max(0.0, eq - float(self.principal_floor))
        return {
            "principal_floor": float(self.principal_floor),
            "principal_equity": float(principal_equity),
            "profit_equity": float(profit_equity),
        }

    # ---------------------------------------------------------------------
    # Fill application (supports long/short + flipping)
    # ---------------------------------------------------------------------
    def apply_fills(self, fills: Iterable[Fill]) -> None:
        """
        Apply fills to cash + positions.

        Conventions:
          - Buy increases quantity, reduces cash.
          - Sell decreases quantity, increases cash.
          - Realized PnL is computed when reducing/closing/flip.
          - Optional `fill.fee` (if present) is subtracted from cash and realized_pnl.
        """
        for f in fills:
            symbol = str(f.symbol)
            price = float(f.price)
            size = float(f.size)

            if size <= 0.0:
                continue

            side = getattr(f, "side", None)
            if side not in ("buy", "sell"):
                raise ValueError(f"Unexpected fill.side={side!r}")

            delta_qty = size if side == "buy" else -size
            fee = float(getattr(f, "fee", 0.0) or 0.0)

            # Cash moves opposite signed notional.
            # Fill.notional is + for buy, - for sell.
            self.cash -= float(f.notional)
            if fee != 0.0:
                self.cash -= fee
                self.fees_paid += fee
                self.realized_pnl -= fee

            pos = self._pos(symbol)
            old_qty = float(pos.quantity)
            old_avg = float(pos.avg_price)

            # Update position logic
            if abs(old_qty) < 1e-12:
                # Opening a fresh position
                pos.quantity = float(delta_qty)
                pos.avg_price = float(price)
                pos.mark_price = float(price)
                continue

            new_qty = old_qty + float(delta_qty)

            # Case A: same direction add (increase magnitude, same sign)
            if (old_qty > 0 and delta_qty > 0) or (old_qty < 0 and delta_qty < 0):
                # Weighted avg by absolute size
                old_abs = abs(old_qty)
                add_abs = abs(delta_qty)
                new_abs = abs(new_qty)
                if new_abs <= 0.0:
                    pos.quantity = 0.0
                    pos.avg_price = 0.0
                else:
                    pos.avg_price = (old_avg * old_abs + price * add_abs) / new_abs
                    pos.quantity = new_qty
                pos.mark_price = float(price)
                continue

            # Case B: reducing/closing/flip (opposite direction trade)
            if old_qty > 0 and delta_qty < 0:
                # Selling a long
                close_qty = min(old_qty, abs(delta_qty))
                self.realized_pnl += (price - old_avg) * close_qty

                if new_qty > 1e-12:
                    # Still long
                    pos.quantity = new_qty
                    # avg stays same for remaining shares
                    pos.avg_price = old_avg
                elif abs(new_qty) <= 1e-12:
                    # Flat
                    pos.quantity = 0.0
                    pos.avg_price = 0.0
                else:
                    # Flipped to short
                    pos.quantity = new_qty  # negative
                    pos.avg_price = price
                pos.mark_price = float(price)
                continue

            if old_qty < 0 and delta_qty > 0:
                # Buying to cover a short
                close_qty = min(abs(old_qty), delta_qty)
                self.realized_pnl += (old_avg - price) * close_qty

                if new_qty < -1e-12:
                    # Still short
                    pos.quantity = new_qty
                    pos.avg_price = old_avg
                elif abs(new_qty) <= 1e-12:
                    # Flat
                    pos.quantity = 0.0
                    pos.avg_price = 0.0
                else:
                    # Flipped to long
                    pos.quantity = new_qty  # positive
                    pos.avg_price = price
                pos.mark_price = float(price)
                continue

            # If we get here, something is inconsistent.
            raise RuntimeError(
                f"Unhandled position transition old_qty={old_qty}, delta_qty={delta_qty}"
            )

    # ---------------------------------------------------------------------
    # Snapshot for logs/UI/backtests
    # ---------------------------------------------------------------------
    def snapshot(self, prices: Mapping[str, float]) -> Dict[str, object]:
        """
        Return a fully-serializable snapshot matching your current CLI output shape.
        """
        self.mark_to_market(prices)
        self._recompute_pools_and_flags()

        eq = self.equity()
        gross = self.gross_exposure()
        net = self.net_exposure()
        unreal = self.unrealized_pnl()
        pools = self.pools()

        positions_out: Dict[str, Dict[str, float]] = {}
        for sym, p in self.positions.items():
            if abs(float(p.quantity)) < 1e-12:
                continue
            positions_out[sym] = {
                "quantity": float(p.quantity),
                "avg_price": float(p.avg_price),
                "mark_price": float(p.mark_price),
                "market_value": float(p.market_value()),
                "unrealized_pnl": float(p.unrealized_pnl()),
            }

        return {
            "cash": float(self.cash),
            "starting_cash": float(self.starting_cash),
            "principal_floor": float(self.principal_floor),
            "realized_pnl": float(self.realized_pnl),
            "unrealized_pnl": float(unreal),
            "fees_paid": float(self.fees_paid),
            "equity": float(eq),
            "gross_exposure": float(gross),
            "net_exposure": float(net),
            "aggressive_enabled": bool(self.aggressive_enabled),
            "halted": bool(self.halted),
            "halted_reason": self.halted_reason,
            "pools": pools,
            "positions": positions_out,
        }
