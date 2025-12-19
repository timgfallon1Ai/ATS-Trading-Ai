from __future__ import annotations

import argparse
import math
from datetime import datetime, timedelta
from typing import List, Sequence

from ats.risk_manager import RiskConfig, RiskManager
from ats.trader.order_types import Order
from ats.trader.trader import Trader

from .backtest_config import BacktestConfig
from .engine import BacktestEngine, BacktestResult
from .types import Bar


class SimpleMAStrategy:
    """Simple moving-average crossover demo strategy (long/short).

    This is intentionally simplistic and exists to validate the Backtester2 loop
    end-to-end (bars -> strategy -> optional risk -> trader -> portfolio).
    """

    def __init__(self, window: int = 20, unit_size: float = 10.0) -> None:
        self.window = max(2, int(window))
        self.unit_size = float(unit_size)
        self._prices: List[float] = []
        self._position: float = 0.0

    def __call__(self, bar: Bar, trader: Trader) -> Sequence[Order]:
        self._prices.append(float(bar.close))
        if len(self._prices) < self.window:
            return []

        window_prices = self._prices[-self.window :]
        ma = sum(window_prices) / float(self.window)

        target = 0.0
        if bar.close > ma:
            target = self.unit_size
        elif bar.close < ma:
            target = -self.unit_size

        delta = target - self._position
        if abs(delta) < 1e-9:
            return []

        side = "buy" if delta > 0 else "sell"
        size = abs(delta)

        self._position = target
        return [Order(symbol=bar.symbol, side=side, size=size, order_type="market")]


def generate_synthetic_bars(
    *, symbol: str, days: int = 200, start_price: float = 100.0
) -> List[Bar]:
    """Generate deterministic, synthetic OHLCV bars for smoke testing."""
    bars: List[Bar] = []

    start_dt = datetime(2025, 1, 1, 9, 30)
    price = float(start_price)

    for i in range(int(days)):
        t = i / 20.0
        drift = 0.05 * i
        delta = 2.0 * math.sin(t)
        close = max(1.0, price + delta + drift / 100.0)

        high = close + 0.5
        low = max(0.5, close - 0.5)
        open_ = (high + low) / 2.0
        volume = float(1_000 + i * 10)

        ts = (start_dt + timedelta(days=i)).isoformat()

        bars.append(
            Bar(
                timestamp=ts,
                symbol=symbol,
                open=float(open_),
                high=float(high),
                low=float(low),
                close=float(close),
                volume=volume,
            )
        )
        price = close

    return bars


def run_backtest(
    *, symbol: str, days: int = 200, enable_risk: bool = True
) -> BacktestResult:
    config = BacktestConfig(symbol=symbol.upper())

    trader = Trader(starting_capital=config.starting_capital)

    bars = generate_synthetic_bars(symbol=config.symbol, days=days)
    strategy = SimpleMAStrategy(window=20, unit_size=10.0)

    risk_manager: RiskManager | None = None
    if enable_risk:
        risk_manager = RiskManager(config=RiskConfig())

    engine = BacktestEngine(
        config=config,
        trader=trader,
        bars=bars,
        strategy=strategy,
        risk_manager=risk_manager,
    )
    return engine.run()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ATS Backtester2 (T2) demo runner")
    parser.add_argument("--symbol", default="AAPL", help="Symbol to backtest")
    parser.add_argument(
        "--days", type=int, default=200, help="Number of bars to simulate"
    )
    parser.add_argument(
        "--no-risk",
        action="store_true",
        help="Disable RiskManager; send strategy orders directly to Trader.",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)

    result = run_backtest(
        symbol=args.symbol,
        days=args.days,
        enable_risk=not args.no_risk,
    )

    print("Backtest complete.")
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
