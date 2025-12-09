from __future__ import annotations

import argparse
import math
from datetime import datetime, timedelta
from typing import Iterable, List, Sequence

from ats.trader.trader import Trader
from ats.trader.order_types import Order
from ats.risk_manager import RiskConfig, RiskManager

from .backtest_config import BacktestConfig
from .engine import BacktestEngine, BacktestResult
from .types import Bar


def generate_synthetic_bars(
    symbol: str,
    days: int = 200,
    start_price: float = 100.0,
) -> List[Bar]:
    """
    Generate a simple, deterministic synthetic price series.

    We use a slow sinusoidal pattern plus a mild trend to make sure
    the strategy has something to react to, but keep it deterministic
    so runs are reproducible.
    """
    bars: List[Bar] = []

    start_dt = datetime(2025, 1, 1, 9, 30)

    price = start_price
    for i in range(days):
        t = i / 20.0  # frequency of the sine wave
        drift = 0.05 * i  # slow upward drift
        delta = 2.0 * math.sin(t)
        close = max(1.0, price + delta + drift / 100.0)

        high = close + 0.5
        low = max(0.5, close - 0.5)
        open_ = (high + low) / 2.0
        volume = 1_000 + i * 10

        ts = (start_dt + timedelta(days=i)).isoformat()

        bars.append(
            Bar(
                timestamp=ts,
                symbol=symbol,
                open=open_,
                high=high,
                low=low,
                close=close,
                volume=volume,
            )
        )

        price = close

    return bars


class SimpleMAStrategy:
    """
    Very simple moving-average crossover-like strategy.

    - Maintains a rolling price window (lookback).
    - Goes long when price is above the moving average.
    - Exits to flat when price is below the moving average.

    This is only for proving the data -> strategy -> Trader -> risk ->
    result pipeline works end-to-end. We'll replace/extend this with real
    strategies as we move toward production.
    """

    def __init__(self, lookback: int = 20, unit_size: int = 10) -> None:
        self.lookback = lookback
        self.unit_size = unit_size
        self._prices: List[float] = []
        self._position: int = 0  # current number of shares

    def __call__(self, bar: Bar, trader: Trader) -> Sequence[Order]:
        self._prices.append(bar.close)

        if len(self._prices) < self.lookback:
            return []

        window = self._prices[-self.lookback :]
        ma = sum(window) / len(window)

        orders: List[Order] = []

        # Long when price > MA, flat when price < MA.
        if bar.close > ma and self._position <= 0:
            # Increase position to +unit_size
            target = self.unit_size
            delta = target - self._position
            if delta > 0:
                orders.append(Order(symbol=bar.symbol, side="buy", size=float(delta)))
                self._position += delta

        elif bar.close < ma and self._position > 0:
            # Exit any existing long position
            delta = self._position
            orders.append(Order(symbol=bar.symbol, side="sell", size=float(delta)))
            self._position -= delta

        return orders


def run_backtest(
    symbol: str,
    days: int = 200,
    enable_risk: bool = True,
) -> BacktestResult:
    """
    Convenience function for running a backtest programmatically.
    """

    config = BacktestConfig(symbol=symbol)
    trader = Trader(starting_capital=config.starting_capital)

    bars = generate_synthetic_bars(symbol=symbol, days=days)
    strategy = SimpleMAStrategy()

    risk_manager: RiskManager | None
    if enable_risk:
        risk_cfg = RiskConfig()
        risk_manager = RiskManager(config=risk_cfg)
    else:
        risk_manager = None

    engine = BacktestEngine(
        config=config,
        trader=trader,
        bars=bars,
        strategy=strategy,
        risk_manager=risk_manager,
    )

    return engine.run()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a simple synthetic backtest using ats.backtester2.",
    )
    parser.add_argument(
        "--symbol",
        required=True,
        help="Symbol to backtest (e.g. AAPL).",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=200,
        help="Number of synthetic daily bars to generate (default: 200).",
    )
    parser.add_argument(
        "--no-risk",
        action="store_true",
        help="Disable the baseline RiskManager for this run.",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)

    result = run_backtest(
        symbol=args.symbol,
        days=args.days,
        enable_risk=not args.no_risk,
    )

    print(f"Backtest complete for {result.config.symbol}")
    print(f"Bars processed: {args.days}")
    print(f"Trades executed: {len(result.trade_history)}")

    if result.final_portfolio is not None:
        print("Final portfolio snapshot:")
        print(result.final_portfolio)
    else:
        print("No trades were executed; no final portfolio snapshot available.")

    if result.risk_decisions:
        blocked = sum(len(d.rejected_orders) for d in result.risk_decisions)
        print(f"Risk manager evaluated {len(result.risk_decisions)} bars.")
        print(f"Orders blocked by risk: {blocked}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
