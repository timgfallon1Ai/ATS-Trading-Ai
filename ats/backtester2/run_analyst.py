from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd

from ats.analyst.analyst_engine import AnalystEngine
from ats.analyst.registry import make_strategies


@dataclass
class PortfolioState:
    cash: float
    position: int
    last_price: float

    @property
    def equity(self) -> float:
        return self.cash + self.position * self.last_price


def generate_synthetic_bars(symbol: str, days: int) -> pd.DataFrame:
    """Very small price simulator so the analyst stack can be exercised."""

    rng = np.random.default_rng(seed=42)
    dates = pd.date_range(end=pd.Timestamp.utcnow().normalize(), periods=days, freq="B")

    prices = [100.0]
    for _ in range(1, days):
        # Simple log-normal random walk with mild drift.
        step = rng.normal(loc=0.0005, scale=0.02)
        prices.append(prices[-1] * float(np.exp(step)))

    prices_arr = np.array(prices)
    high = prices_arr * (1.0 + rng.uniform(0.0, 0.01, size=days))
    low = prices_arr * (1.0 - rng.uniform(0.0, 0.01, size=days))
    open_ = prices_arr * (1.0 + rng.uniform(-0.005, 0.005, size=days))
    volume = rng.integers(low=1_000_000, high=5_000_000, size=days)

    df = pd.DataFrame(
        {
            "timestamp": dates,
            "symbol": symbol,
            "open": open_,
            "high": high,
            "low": low,
            "close": prices_arr,
            "volume": volume,
        }
    )

    return df.reset_index(drop=True)


def run_backtest(symbol: str, days: int, starting_cash: float = 100_000.0) -> None:
    bars = generate_synthetic_bars(symbol, days)

    strategies = make_strategies()
    engine = AnalystEngine(strategies=strategies)

    state = PortfolioState(
        cash=starting_cash,
        position=0,
        last_price=float(bars["close"].iloc[0]),
    )

    trades: List[Dict[str, object]] = []
    allocations: List[Dict[str, object]] = []

    for idx, row in bars.iterrows():
        history = bars.iloc[: idx + 1]
        price = float(row["close"])
        ts = pd.Timestamp(row["timestamp"])

        state.last_price = price

        alloc = engine.evaluate(symbol=symbol, history=history, timestamp=ts)
        allocations.append(alloc)

        score = float(alloc["score"])
        confidence = float(alloc["confidence"])

        # Target exposure in [-1, 1]
        target_exposure = score * confidence
        max_notional = state.equity

        desired_notional = target_exposure * max_notional
        desired_position = int(desired_notional / price)

        delta = desired_position - state.position
        if delta == 0:
            continue

        trade_notional = delta * price

        state.cash -= trade_notional
        state.position += delta

        trades.append(
            {
                "timestamp": ts,
                "symbol": symbol,
                "qty": delta,
                "price": price,
                "notional": trade_notional,
                "score": score,
                "confidence": confidence,
            }
        )

    final_price = float(bars["close"].iloc[-1])
    state.last_price = final_price

    final_equity = state.equity
    pnl = final_equity - starting_cash

    print(f"Analyst backtest complete for {symbol}")
    print(f"Bars processed: {len(bars)}")
    print(f"Trades executed: {len(trades)}")
    print(
        "Final portfolio snapshot:",
        {
            "cash": state.cash,
            "equity": final_equity,
            "position": state.position,
            "last_price": state.last_price,
            "realized_pnl": pnl,
        },
    )

    long_signals = sum(1 for a in allocations if float(a["score"]) > 0.0)
    short_signals = sum(1 for a in allocations if float(a["score"]) < 0.0)
    flat_signals = len(allocations) - long_signals - short_signals

    print(
        "Signal breakdown:",
        {"long": long_signals, "short": short_signals, "flat": flat_signals},
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run analyst-driven synthetic backtest."
    )
    parser.add_argument("--symbol", required=True, help="Ticker symbol to backtest")
    parser.add_argument(
        "--days", type=int, default=200, help="Number of business days to simulate"
    )
    parser.add_argument(
        "--starting-cash",
        type=float,
        default=100_000.0,
        help="Starting cash balance for the portfolio.",
    )

    args = parser.parse_args()
    run_backtest(symbol=args.symbol, days=args.days, starting_cash=args.starting_cash)


if __name__ == "__main__":
    main()
