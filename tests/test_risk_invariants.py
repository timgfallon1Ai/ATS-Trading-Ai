from __future__ import annotations

from ats.risk_manager.risk_manager import RiskConfig, RiskManager
from ats.trader.order_types import Order


def test_portfolio_halted_blocks_all_orders() -> None:
    rm = RiskManager(config=RiskConfig(enforce_portfolio_halt=True))

    bar = {"timestamp": "t", "symbol": "AAPL", "close": 100.0}
    order = Order(symbol="AAPL", side="buy", size=1.0, order_type="market")

    portfolio = {
        "equity": 99_000.0,
        "principal_floor": 100_000.0,
        "halted": True,
        "halted_reason": "unit_test_halt",
        "gross_exposure": 0.0,
        "net_exposure": 0.0,
        "positions": {},
        "pools": {"principal_floor": 100_000.0, "profit_equity": 0.0},
    }

    decision = rm.evaluate_orders(bar, [order], portfolio=portfolio)

    assert decision.accepted_orders == []
    assert len(decision.rejected_orders) == 1
    assert "portfolio_halted" in decision.rejected_orders[0].reason


def test_gross_exposure_cap_blocks_order() -> None:
    # Make the principal-mode gross cap very tight: 1% of principal_floor
    cfg = RiskConfig(
        enforce_exposure_caps=True,
        max_gross_exposure_principal_frac=0.01,  # 1% of floor
        max_net_exposure_principal_frac=0.50,  # irrelevant for this test
        max_symbol_exposure_frac=1.0,
    )
    rm = RiskManager(config=cfg)

    bar = {"timestamp": "t", "symbol": "AAPL", "close": 100.0}

    # Principal floor = 100k => gross cap = 1000
    # Existing gross exposure = 900; buying 2 @ 100 => gross becomes 1100 > 1000 => reject.
    portfolio = {
        "equity": 100_000.0,
        "principal_floor": 100_000.0,
        "gross_exposure": 900.0,
        "net_exposure": 0.0,
        "positions": {},
        "pools": {"principal_floor": 100_000.0, "profit_equity": 0.0},
        "aggressive_enabled": False,
    }

    order = Order(symbol="AAPL", side="buy", size=2.0, order_type="market")
    decision = rm.evaluate_orders(bar, [order], portfolio=portfolio)

    assert decision.accepted_orders == []
    assert len(decision.rejected_orders) == 1
    assert "gross_exposure_cap" in decision.rejected_orders[0].reason
