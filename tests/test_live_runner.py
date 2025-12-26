from __future__ import annotations

from datetime import datetime, timezone

from ats.live.config import LiveConfig
from ats.live.paper_broker import PaperBroker
from ats.live.runner import LiveRunner
from ats.live.types import PriceTick
from ats.live.strategies.buy_and_hold import BuyAndHoldStrategy


class _FakeMarketData:
    def __init__(self, price_by_symbol):
        self._prices = dict(price_by_symbol)

    def get_last_trade(self, symbol: str) -> PriceTick:
        return PriceTick(
            symbol=symbol,
            price=float(self._prices[symbol]),
            timestamp=datetime.now(tz=timezone.utc),
            source="fake",
        )


def test_live_runner_buy_and_hold_paper_executes_once_per_symbol():
    cfg = LiveConfig(
        symbols=["AAA", "BBB"],
        market_data="mock",
        broker="paper",
        poll_seconds=0.0,
        max_ticks=3,
        execute=True,
        flatten_on_kill=False,
        strategy="buy_and_hold",
        notional_per_symbol=100.0,
        allow_fractional=False,
        run_tag="test",
        mock_prices={"AAA": 10.0, "BBB": 20.0},
    )

    broker = PaperBroker(starting_cash=10_000.0)
    md = _FakeMarketData({"AAA": 10.0, "BBB": 20.0})
    strat = BuyAndHoldStrategy(notional_per_symbol=100.0, allow_fractional=False)

    runner = LiveRunner(
        config=cfg,
        broker=broker,
        market_data=md,
        strategy=strat,
        kill_switch_fn=lambda: False,
        sleep_fn=lambda _: None,
    )

    runner.run()

    state = broker.get_state()
    # 100 notional at $10 => 10 shares
    assert state.positions.get("AAA") == 10.0
    # 100 notional at $20 => 5 shares
    assert state.positions.get("BBB") == 5.0
