import subprocess
import sys

from ats.backtester2.run import run_backtest


def test_backtester2_ensemble_programmatic_smoke() -> None:
    res = run_backtest(symbol="AAPL", days=60, enable_risk=False, strategy="ensemble")
    assert res.config.symbol == "AAPL"
    assert isinstance(res.trade_history, list)
    assert isinstance(res.portfolio_history, list)


def test_backtester2_cli_accepts_strategy_flag() -> None:
    cmd = [
        sys.executable,
        "-m",
        "ats.backtester2.run",
        "--symbol",
        "AAPL",
        "--days",
        "40",
        "--no-risk",
        "--strategy",
        "ensemble",
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    assert p.returncode == 0, (p.stdout, p.stderr)
    assert "Backtest complete" in (p.stdout + p.stderr)
