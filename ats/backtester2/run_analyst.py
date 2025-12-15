from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from ats.aggregator.aggregator import Aggregator
from ats.analyst.analyst_engine import AnalystEngine
from ats.analyst.registry import make_strategies
from ats.risk_manager.rm_bridge import batch_to_capital_packets


@dataclass
class BacktestResult:
    symbol: str
    bars_processed: int
    trades_executed: int
    cash: float
    equity: float
    position: int
    last_price: float
    realized_pnl: float
    signal_breakdown: Dict[str, int]


def _generate_synthetic_history(symbol: str, days: int, seed: int) -> pd.DataFrame:
    """Generate a simple synthetic OHLCV history for local analyst testing."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range(end=pd.Timestamp.utcnow().normalize(), periods=days, freq="D")

    prices = 100.0 + rng.normal(scale=1.0, size=days).cumsum()
    prices = np.maximum(prices, 1.0)

    close = prices
    open_ = close * (1.0 + rng.normal(0.0, 0.002, size=days))
    high = np.maximum(open_, close) * (1.0 + np.abs(rng.normal(0.0, 0.002, size=days)))
    low = np.minimum(open_, close) * (1.0 - np.abs(rng.normal(0.0, 0.002, size=days)))
    volume = rng.integers(100_000, 1_000_000, size=days)

    df = pd.DataFrame(
        {
            "timestamp": dates,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )
    return df


def run_backtest(symbol: str, days: int, seed: int = 42) -> BacktestResult:
    history = _generate_synthetic_history(symbol, days, seed)

    engine = AnalystEngine(strategies=make_strategies())
    aggregator = Aggregator()

    allocations: List[Dict[str, Any]] = []

    starting_equity = 100_000.0
    cash = starting_equity
    position = 0
    trades = 0
    last_price = float(history["close"].iloc[0])

    for idx, row in history.iterrows():
        window = history.iloc[: idx + 1].copy()
        timestamp = row["timestamp"]

        allocation = engine.evaluate(symbol=symbol, history=window, timestamp=timestamp)
        allocations.append(allocation)

        combined = aggregator.combine_allocation(allocation)
        direction = combined["direction"]
        price = float(row["close"])

        if direction == "long":
            if position <= 0:
                if position < 0:
                    cash += -position * price
                    trades += 1
                cash -= price
                position = 1
                trades += 1
        elif direction == "short":
            if position >= 0:
                if position > 0:
                    cash += position * price
                    trades += 1
                cash += price
                position = -1
                trades += 1

        last_price = price

    equity = cash + position * last_price
    realized_pnl = equity - starting_equity

    batch = aggregator.prepare_batch(allocations)
    combined_signals = batch["combined_signals"]
    normalized_allocs = batch["allocations"]

    signal_breakdown = {
        "long": sum(1 for s in combined_signals if s.get("direction") == "long"),
        "short": sum(1 for s in combined_signals if s.get("direction") == "short"),
        "flat": sum(1 for s in combined_signals if s.get("direction") == "flat"),
    }

    # --- Logging: full CombinedSignal + allocation per bar ---
    log_dir = Path("analyst_logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"analyst_backtest_{symbol}.jsonl"

    with log_path.open("w", encoding="utf-8") as f:
        for sig, alloc in zip(combined_signals, normalized_allocs):
            record = {
                "symbol": symbol,
                "timestamp": sig.get("timestamp"),
                "signal": sig,
                "allocation": alloc,
            }
            f.write(json.dumps(record) + "\n")

    # --- RM bridge: turn aggregated allocations into CapitalAllocPacket set ---
    rm_packets = batch_to_capital_packets(batch, base_capital=starting_equity)
    rm_log_path = log_dir / f"analyst_backtest_{symbol}_rm.jsonl"
    with rm_log_path.open("w", encoding="utf-8") as f_rm:
        for pkt in rm_packets:
            f_rm.write(json.dumps(pkt) + "\n")

    print(f"Analyst backtest log written to {log_path}")
    print(f"RM bridge packets written to {rm_log_path}")
    if rm_packets:
        print("RM bridge preview (first 3 packets):")
        for pkt in rm_packets[:3]:
            print("  ", pkt)

    result = BacktestResult(
        symbol=symbol,
        bars_processed=len(history),
        trades_executed=trades,
        cash=cash,
        equity=equity,
        position=position,
        last_price=last_price,
        realized_pnl=realized_pnl,
        signal_breakdown=signal_breakdown,
    )

    print(f"Analyst backtest complete for {symbol}")
    print(f"Bars processed: {result.bars_processed}")
    print(f"Trades executed: {result.trades_executed}")
    print(
        "Final portfolio snapshot:",
        {
            "cash": result.cash,
            "equity": result.equity,
            "position": result.position,
            "last_price": result.last_price,
            "realized_pnl": result.realized_pnl,
        },
    )
    print("Signal breakdown:", result.signal_breakdown)

    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synthetic analyst backtester using the full AnalystEngine."
    )
    parser.add_argument("--symbol", type=str, default="AAPL")
    parser.add_argument("--days", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    run_backtest(symbol=args.symbol, days=args.days, seed=args.seed)


if __name__ == "__main__":
    main()
