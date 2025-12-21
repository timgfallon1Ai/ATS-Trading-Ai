from __future__ import annotations


def test_backtester2_cli_runs(run_module) -> None:
    # Keep days modest so CI stays fast
    res = run_module("ats.backtester2.run", ["--symbol", "AAPL", "--days", "50"])
    assert res.returncode == 0, res.output
    assert "Backtest complete" in res.stdout, res.output


def test_backtester2_cli_runs_without_risk(run_module) -> None:
    # Your CLI has --no-risk based on your terminal output
    res = run_module(
        "ats.backtester2.run", ["--symbol", "AAPL", "--days", "50", "--no-risk"]
    )
    assert res.returncode == 0, res.output
    assert "Backtest complete" in res.stdout, res.output
