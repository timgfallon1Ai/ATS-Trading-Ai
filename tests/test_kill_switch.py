from __future__ import annotations

from pathlib import Path

import pytest

from ats.backtester2.backtest_config import BacktestConfig
from ats.backtester2.engine import BacktestEngine
from ats.backtester2.types import Bar
from ats.core.kill_switch import (
    disable_kill_switch,
    enable_kill_switch,
    kill_switch_engaged,
)
from ats.trader.order_types import Order
from ats.trader.trader import Trader


def test_kill_switch_file_toggle(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    kill_file = tmp_path / "KILL_SWITCH_TEST"
    monkeypatch.setenv("ATS_KILL_SWITCH_FILE", str(kill_file))

    disable_kill_switch()
    assert kill_switch_engaged() is False

    enable_kill_switch(reason="unit_test")
    assert kill_switch_engaged() is True

    disable_kill_switch()
    assert kill_switch_engaged() is False


def test_backtester_flattens_when_kill_switch_engaged(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    kill_file = tmp_path / "KILL_SWITCH_TEST"
    monkeypatch.setenv("ATS_KILL_SWITCH_FILE", str(kill_file))
    disable_kill_switch()

    bars = [
        Bar(
            timestamp="t0",
            symbol="AAPL",
            open=100.0,
            high=100.0,
            low=100.0,
            close=100.0,
            volume=0.0,
        ),
        Bar(
            timestamp="t1",
            symbol="AAPL",
            open=100.0,
            high=100.0,
            low=100.0,
            close=100.0,
            volume=0.0,
        ),
    ]

    trader = Trader(starting_capital=100_000.0)

    state = {"first": True}

    def strat(bar: Bar, _trader: Trader):
        if state["first"]:
            state["first"] = False
            # Enable kill switch DURING the first bar; engine checks at start of next bar.
            enable_kill_switch(reason="unit_midrun")
            return [
                Order(symbol=bar.symbol, side="buy", size=10.0, order_type="market")
            ]
        # If engine calls strategy on bar2, it would mean kill-switch check failed.
        return [Order(symbol=bar.symbol, side="buy", size=10.0, order_type="market")]

    engine = BacktestEngine(
        config=BacktestConfig(
            symbol="AAPL", starting_capital=100_000.0, bar_limit=None
        ),
        trader=trader,
        bars=bars,
        strategy=strat,
        risk_manager=None,
    )

    result = engine.run()
    fp = result.final_portfolio or {}
    positions = fp.get("positions", {}) if isinstance(fp, dict) else {}

    # After kill-switch, engine must flatten, so positions snapshot should be empty.
    assert positions == {} or all(
        abs(v.get("quantity", 0.0)) < 1e-9 for v in positions.values()
    )

    disable_kill_switch()
