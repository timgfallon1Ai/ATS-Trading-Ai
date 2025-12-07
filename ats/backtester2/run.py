from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

from ats.trader.order_types import Order
from ats.trader.trader import Trader


@dataclass
class Bar:
    timestamp: datetime
    symbol: str
    close: float


def load_bars_from_csv(path: Path, symbol: str) -> List[Bar]:
    """
    Minimal CSV loader.

    Expects a CSV with at least:
        timestamp,symbol,close

    - timestamp: ISO string or any format parseable by datetime.fromisoformat
    - symbol: ticker
    - close: float
    """
    bars: List[Bar] = []
    with path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("symbol") != symbol:
                continue
            ts_raw = row.get("timestamp") or row.get("time") or row.get("date")
            if not ts_raw:
                continue
            try:
                ts = datetime.fromisoformat(ts_raw)
            except Exception:
                # Fallback: keep as string, we mostly care about order
                ts = datetime.strptime(ts_raw, "%Y-%m-%d")
            close = float(row["close"])
            bars.append(Bar(timestamp=ts, symbol=symbol, close=close))
    bars.sort(key=lambda b: b.timestamp)
    return bars


def generate_synthetic_bars(symbol: str, n: int = 50) -> List[Bar]:
    """Fallback: simple synthetic walk if no CSV is provided."""
    price = 100.0
    bars: List[Bar] = []
    ts = datetime.utcnow()
    for i in range(n):
        # deterministic-ish walk
        price *= 1.0 + (0.01 if i % 5 == 0 else -0.005)
        bars.append(Bar(timestamp=ts, symbol=symbol, close=price))
        ts = ts.replace(second=(ts.second + 1) % 60)
    return bars


def simple_strategy(bars: Iterable[Bar]) -> Iterable[List[Order]]:
    """
    Example strategy:

    - First bar: buy 10 shares.
    - Last bar: sell all.
    - Otherwise: hold.
    """
    bars = list(bars)
    n = len(bars)
    if n == 0:
        return []

    orders_per_bar: List[List[Order]] = [[] for _ in range(n)]

    # Buy on first bar
    first = bars[0]
    orders_per_bar[0] = [Order(symbol=first.symbol, side="buy", size=10)]

    # Sell all on last bar; actual size will be computed based on portfolio state
    last = bars[-1]
    orders_per_bar[-1] = [Order(symbol=last.symbol, side="sell", size=10)]

    return orders_per_bar


def run_backtest(
    symbol: str,
    csv_path: Optional[Path],
    starting_capital: float = 1_000.0,
) -> None:
    if csv_path is not None and csv_path.exists():
        bars = load_bars_from_csv(csv_path, symbol=symbol)
    else:
        bars = generate_synthetic_bars(symbol=symbol, n=50)

    if not bars:
        print("No bars loaded; nothing to backtest.")
        return

    trader = Trader(starting_capital=starting_capital)
    orders_per_bar = list(simple_strategy(bars))

    print(f"Running backtest for {symbol} with {len(bars)} bars...")
    for bar, orders in zip(bars, orders_per_bar):
        trader.update_market({bar.symbol: bar.close})
        res = trader.process_orders(orders)
        portfolio = res["portfolio"]
        print(
            f"{bar.timestamp.isoformat()}  "
            f"px={bar.close:.2f}  "
            f"equity={portfolio['equity']:.2f}  "
            f"cash={portfolio['cash']:.2f}  "
            f"pos={portfolio['positions']}"
        )

    final_snapshot = trader.portfolio.snapshot({bars[-1].symbol: bars[-1].close})
    print("\n=== Backtest complete ===")
    print(f"Final equity: {final_snapshot['equity']:.2f}")
    print(f"Realized PnL: {final_snapshot['realized_pnl']:.2f}")
    print(f"Positions: {final_snapshot['positions']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run backtest2 using T1 Trader.")
    parser.add_argument(
        "--symbol", type=str, default="AAPL", help="Symbol to backtest."
    )
    parser.add_argument(
        "--csv",
        type=str,
        default="",
        help="Optional path to CSV with columns [timestamp,symbol,close].",
    )
    parser.add_argument(
        "--capital",
        type=float,
        default=1_000.0,
        help="Starting capital for the portfolio.",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv) if args.csv else None
    run_backtest(
        symbol=args.symbol,
        csv_path=csv_path,
        starting_capital=args.capital,
    )


if __name__ == "__main__":
    main()
