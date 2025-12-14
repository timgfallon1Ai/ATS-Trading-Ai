from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import math
import random
from typing import Any, Dict, List, Literal, Sequence

from ats.aggregator.aggregator import Aggregator


Direction = Literal["long", "short", "flat"]


@dataclasses.dataclass
class CombinedSignal:
    """Per-bar, per-symbol combined analyst view used for logging only."""

    symbol: str
    timestamp: str
    score: float
    confidence: float
    strategy_breakdown: Dict[str, float]


@dataclasses.dataclass
class AggregatedAllocationLog:
    """Slim log wrapper around Aggregator.prepare_batch output."""

    symbol: str
    timestamp: str
    raw_signal: float
    strength: float
    strategy_breakdown: Dict[str, float]


@dataclasses.dataclass
class PortfolioState:
    cash: float = 100_000.0
    position: int = 0
    last_price: float = 0.0
    realized_pnl: float = 0.0

    def equity(self) -> float:
        return self.cash + self.position * self.last_price


def _generate_synthetic_bars(
    symbol: str, days: int, seed: int | None
) -> List[Dict[str, Any]]:
    rng = random.Random(seed)
    price = 100.0
    bars: List[Dict[str, Any]] = []

    for i in range(days):
        # simple geometric random walk
        ret = rng.gauss(0.0005, 0.02)
        prev = price
        price = max(1.0, prev * (1.0 + ret))

        high = max(prev, price) * (1.0 + abs(rng.gauss(0.0, 0.005)))
        low = min(prev, price) * (1.0 - abs(rng.gauss(0.0, 0.005)))
        volume = rng.uniform(200_000, 1_000_000)
        ts = (dt.datetime.utcnow() - dt.timedelta(days=days - i)).isoformat()

        bars.append(
            {
                "symbol": symbol,
                "timestamp": ts,
                "open": prev,
                "high": high,
                "low": low,
                "close": price,
                "volume": volume,
            }
        )

    return bars


def _compute_features(bars: Sequence[Dict[str, Any]]) -> List[Dict[str, float]]:
    """Very small feature set just to drive toy strategies."""
    features: List[Dict[str, float]] = []
    closes = [b["close"] for b in bars]

    for i, bar in enumerate(bars):
        row: Dict[str, float] = {}
        if i > 0:
            row["ret_1"] = (closes[i] / closes[i - 1]) - 1.0
        else:
            row["ret_1"] = 0.0

        window = 5
        if i >= window:
            window_closes = closes[i - window + 1 : i + 1]
            mean = sum(window_closes) / window
            var = sum((c - mean) ** 2 for c in window_closes) / window
            std = math.sqrt(var)
            row["zscore_5"] = (closes[i] - mean) / std if std > 0 else 0.0
        else:
            row["zscore_5"] = 0.0

        vol_window = 10
        if i >= vol_window:
            win = closes[i - vol_window + 1 : i + 1]
            mean = sum(win) / vol_window
            var = sum((c - mean) ** 2 for c in win) / vol_window
            row["vol_10"] = math.sqrt(var)
        else:
            row["vol_10"] = 0.0

        features.append(row)

    return features


def _toy_strategy_scores(feat: Dict[str, float]) -> Dict[str, float]:
    """Three tiny toy strategies: momentum, mean reversion, volatility breakout."""
    scores: Dict[str, float] = {}

    z = feat.get("zscore_5", 0.0)
    # Momentum: follow z-score sign
    scores["momentum"] = float(z)

    # Mean reversion: opposite of momentum
    scores["mean_reversion"] = float(-z)

    # Vol breakout: cheap convexity on realized volatility
    vol = feat.get("vol_10", 0.0)
    scores["vol_breakout"] = float(vol / 10.0)

    return scores


def _combine_strategies(
    symbol: str, ts: str, strat_scores: Dict[str, float]
) -> CombinedSignal:
    if not strat_scores:
        return CombinedSignal(
            symbol=symbol,
            timestamp=ts,
            score=0.0,
            confidence=0.0,
            strategy_breakdown={},
        )

    # Equal weights for now
    total = sum(abs(v) for v in strat_scores.values()) or 1.0
    score = sum(v for v in strat_scores.values()) / len(strat_scores)
    # Confidence rises with total absolute signal but is clipped
    confidence = min(1.0, total / len(strat_scores))

    return CombinedSignal(
        symbol=symbol,
        timestamp=ts,
        score=float(score),
        confidence=float(confidence),
        strategy_breakdown={k: float(v) for k, v in strat_scores.items()},
    )


def run_backtest(
    symbol: str,
    days: int,
    seed: int | None = None,
    max_position: int = 50,
    trade_cap: int | None = None,
) -> None:
    bars = _generate_synthetic_bars(symbol=symbol, days=days, seed=seed)
    feats = _compute_features(bars)

    agg = Aggregator()
    portfolio = PortfolioState()
    trades_executed = 0
    signal_counts: Dict[Direction, int] = {"long": 0, "short": 0, "flat": 0}

    last_combined: CombinedSignal | None = None
    last_allocation: AggregatedAllocationLog | None = None

    for i, bar in enumerate(bars):
        price = bar["close"]
        portfolio.last_price = price

        feature_row = feats[i]
        strat_scores = _toy_strategy_scores(feature_row)
        combined = _combine_strategies(symbol, bar["timestamp"], strat_scores)
        last_combined = combined

        # Track discrete direction for summary
        if combined.score > 0.0:
            direction: Direction = "long"
        elif combined.score < 0.0:
            direction = "short"
        else:
            direction = "flat"
        signal_counts[direction] += 1

        # Build minimal H1-B style analyst output for Aggregator
        analyst_output = {
            symbol: {
                "signal": combined.score,
                "confidence": combined.confidence,
                "features": feature_row,
                "strategy_breakdown": combined.strategy_breakdown,
                "meta": {
                    "toy_strategy_scores": strat_scores,
                },
            }
        }

        allocations = agg.prepare_batch(analyst_output)
        alloc = allocations[symbol]

        last_allocation = AggregatedAllocationLog(
            symbol=alloc["symbol"],
            timestamp=alloc["timestamp"],
            raw_signal=float(alloc["raw_signal"]),
            strength=float(alloc["strength"]),
            strategy_breakdown=dict(alloc.get("strategy_breakdown", {})),
        )

        # Convert allocation into an integer target position using strength
        direction_sign = 0
        if alloc["raw_signal"] > 0:
            direction_sign = 1
        elif alloc["raw_signal"] < 0:
            direction_sign = -1

        target_pos = int(round(max_position * alloc["strength"] * direction_sign))

        if trade_cap is not None and trades_executed >= trade_cap:
            # Respect global trade cap by freezing position adjustments
            target_pos = portfolio.position

        delta = target_pos - portfolio.position
        if delta != 0:
            trades_executed += 1

            # Simple market order fill at close
            trade_cost = delta * price
            portfolio.cash -= trade_cost
            # No explicit slippage/fees model here yet
            portfolio.position = target_pos

    # Final equity mark
    equity = portfolio.equity()

    print(f"Analyst backtest complete for {symbol}")
    print(f"Bars processed: {len(bars)}")
    print(f"Trades executed: {trades_executed}")
    print(
        "Final portfolio snapshot:",
        {
            "cash": portfolio.cash,
            "equity": equity,
            "position": portfolio.position,
            "last_price": portfolio.last_price,
            "realized_pnl": portfolio.realized_pnl,
        },
    )
    print("Signal breakdown:", signal_counts)

    # New: expose CombinedSignal + AggregatedAllocation in the logs
    if last_combined is not None and last_allocation is not None:
        print("\nLast bar CombinedSignal:")
        print(dataclasses.asdict(last_combined))
        print("\nLast bar AggregatedAllocation (via Aggregator.prepare_batch):")
        print(dataclasses.asdict(last_allocation))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Synthetic analyst+aggregator backtest driver."
    )
    parser.add_argument("--symbol", type=str, default="AAPL")
    parser.add_argument("--days", type=int, default=200)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--max-position", type=int, default=50)
    parser.add_argument("--trade-cap", type=int, default=None)
    args = parser.parse_args()

    run_backtest(
        symbol=args.symbol,
        days=args.days,
        seed=args.seed,
        max_position=args.max_position,
        trade_cap=args.trade_cap,
    )


if __name__ == "__main__":
    main()
