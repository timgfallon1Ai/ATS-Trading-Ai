from __future__ import annotations

from ats.live.config import LiveConfig
from ats.live.paper_broker import PaperBroker
from ats.live.runner import run_live


def test_live_runner_mock_buy_and_hold_executes() -> None:
    cfg = LiveConfig(
        symbols=["AAA", "BBB"],
        market_data="mock",
        mock_prices={"AAA": 10.0, "BBB": 20.0},
        broker="paper",
        execute=True,
        poll_seconds=0.0,
        max_ticks=2,
        strategy="buy_and_hold",
        notional_per_symbol=100.0,
        allow_fractional=True,
        run_tag="test",
    )

    broker = run_live(cfg)
    assert isinstance(broker, PaperBroker)
    pos = broker.get_positions()
    assert pos.get("AAA", 0.0) > 0
    assert pos.get("BBB", 0.0) > 0


def test_live_runner_mock_analyst_ensemble_smoke() -> None:
    cfg = LiveConfig(
        symbols=["AAA"],
        market_data="mock",
        mock_prices={"AAA": 10.0},
        broker="paper",
        execute=False,  # dry-run: just ensure it runs
        poll_seconds=0.0,
        max_ticks=5,
        strategy="analyst_ensemble",
        notional_per_symbol=100.0,
        allow_fractional=True,
        history_bars=50,
        warmup_bars=1,  # let it evaluate quickly in a smoke test
        min_confidence=0.0,
        log_signals=False,
        run_tag="test",
    )

    broker = run_live(cfg)
    assert broker is not None
