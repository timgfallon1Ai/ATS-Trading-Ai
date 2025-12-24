from ats.backtester2.metrics import compute_backtest_metrics
from ats.backtester2.run import run_backtest


def test_portfolio_history_records_every_bar() -> None:
    res = run_backtest(symbol="AAPL", days=25, enable_risk=False, strategy="ma")
    assert len(res.portfolio_history) == 25

    m = compute_backtest_metrics(res.portfolio_history)
    assert m.n_bars == 25
