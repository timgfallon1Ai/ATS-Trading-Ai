cat > ats / backtester2 / run.py << "EOF"
from __future__ import annotations

import argparse
import math
from datetime import datetime, timedelta
from typing import List, Optional, Sequence

from ats.risk_manager import RiskConfig, RiskManager
from ats.trader.order_types import Order
from ats.trader.trader import Trader

from .backtest_config import BacktestConfig
from .engine import BacktestEngine, BacktestResult
from .types import Bar


def generate_synthetic_bars(
    symbol: str,
    days: int = 200,
    start_price: float = 100.0,
) -> List[Bar]:
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
    def __init__(self, lookback: int = 20, unit_size: int = 10) -> None:
        self.lookback = int(lookback)
        self.unit_size = int(unit_size)
        self._prices: List[float] = []
        self._position: float = 0.0

    def __call__(self, bar: Bar, trader: Trader) -> Sequence[Order]:
        self._prices.append(float(bar.close))
        if len(self._prices) < self.lookback:
            return []

        window = self._prices[-self.lookback :]
        ma = sum(window) / float(len(window))

        orders: List[Order] = []

        if float(bar.close) > ma and self._position <= 0:
            target = float(self.unit_size)
            delta = target - self._position
            if delta > 0:
                orders.append(Order(symbol=bar.symbol, side="buy", size=float(delta)))
                self._position += delta

        elif float(bar.close) < ma and self._position > 0:
            delta = self._position
            if delta > 0:
                orders.append(Order(symbol=bar.symbol, side="sell", size=float(delta)))
                self._position -= delta

        return orders


def run_backtest(
    symbol: str,
    days: int = 200,
    enable_risk: bool = True,
    strategy: str = "ma",
    strategy_names: Optional[Sequence[str]] = None,
    max_position_frac: float = 0.20,
) -> BacktestResult:
    config = BacktestConfig(symbol=symbol, starting_capital=100_000.0, bar_limit=None)
    trader = Trader(starting_capital=float(config.starting_capital))

    bars = generate_synthetic_bars(symbol=symbol, days=int(days))

    risk_manager = RiskManager(RiskConfig()) if enable_risk else None

    strategy_key = (strategy or "ma").strip().lower()
    if strategy_key == "ensemble":
        from .ensemble_strategy import EnsembleStrategy, EnsembleStrategyConfig

        strat = EnsembleStrategy(
            symbol=symbol,
            risk_manager=risk_manager,
            config=EnsembleStrategyConfig(
                strategy_names=strategy_names,
                max_position_frac=float(max_position_frac),
            ),
        )
    else:
        strat = SimpleMAStrategy()

    engine = BacktestEngine(
        config=config,
        trader=trader,
        bars=bars,
        strategy=strat,  # type: ignore[arg-type]
        risk_manager=risk_manager,
    )
    return engine.run()


def _parse_strategy_names(raw: Optional[str]) -> Optional[Sequence[str]]:
    if raw is None:
        return None
    raw_s = str(raw).strip()
    if not raw_s:
        return None
    parts = [p.strip() for p in raw_s.split(",") if p.strip()]
    return parts or None


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a synthetic backtest using ats.backtester2.",
    )
    parser.add_argument("--symbol", required=True, help="Symbol (e.g. AAPL).")
    parser.add_argument(
        "--days", type=int, default=200, help="Bars to generate (default: 200)."
    )
    parser.add_argument("--no-risk", action="store_true", help="Disable RiskManager.")

    parser.add_argument(
        "--strategy",
        choices=["ma", "ensemble"],
        default="ma",
        help="Strategy mode (default: ma).",
    )
    parser.add_argument(
        "--strategies",
        default=None,
        help="Comma-separated analyst strategy names (ensemble only). Default: all.",
    )
    parser.add_argument(
        "--max-position-frac",
        type=float,
        default=0.20,
        help="Max position fraction of capital base (ensemble only).",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)

    result = run_backtest(
        symbol=str(args.symbol),
        days=int(args.days),
        enable_risk=not bool(args.no_risk),
        strategy=str(args.strategy),
        strategy_names=_parse_strategy_names(args.strategies),
        max_position_frac=float(args.max_position_frac),
    )

    print("Backtest complete.")
    print(f"Trades executed: {len(result.trade_history)}")
    print("Final portfolio snapshot:")
    print(result.final_portfolio)

    if result.risk_decisions:
        blocked = sum(len(d.rejected_orders) for d in result.risk_decisions)
        print(f"Risk manager evaluated {len(result.risk_decisions)} bars.")
        print(f"Orders blocked by risk: {blocked}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
EOF
