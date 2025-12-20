from __future__ import annotations

import argparse
from typing import Sequence

from ats.run.boot import BootConfig, boot_system
from ats.run.orchestrator import BacktestRunConfig


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ats.run",
        description="ATS unified runtime entrypoint (backtest-first).",
    )

    parser.add_argument(
        "--log-dir",
        default="logs",
        help="Base directory for run logs (default: logs).",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Override run_id (default: auto-generated).",
    )

    sub = parser.add_subparsers(dest="cmd", required=True)

    bt = sub.add_parser(
        "backtest",
        help="Run Backtester2 (synthetic bars) through the unified runtime wrapper.",
    )
    bt.add_argument("--symbol", required=True, help="Symbol to backtest (e.g. AAPL).")
    bt.add_argument(
        "--days",
        type=int,
        default=200,
        help="Number of synthetic daily bars to generate (default: 200).",
    )
    bt.add_argument(
        "--no-risk",
        action="store_true",
        help="Disable the baseline RiskManager for this run.",
    )

    live = sub.add_parser(
        "live",
        help="Placeholder for future live/paper trading loop (not implemented yet).",
    )
    live.add_argument(
        "--symbol",
        default=None,
        help="(Reserved) Symbol for the live loop.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    reg = boot_system(BootConfig(log_dir=args.log_dir, run_id=args.run_id))

    orch = reg.get("orchestrator")
    if orch is None:
        from ats.run.orchestrator import RuntimeOrchestrator

        orch = RuntimeOrchestrator(log=reg["log"])
        reg.add("orchestrator", orch)

    log = reg["log"]

    if args.cmd == "backtest":
        result = orch.run_backtest(
            BacktestRunConfig(
                symbol=args.symbol,
                days=args.days,
                enable_risk=not args.no_risk,
            )
        )

        print("Backtest complete.")
        print(f"Trades executed: {len(result.trade_history)}")
        print("Final portfolio snapshot:")
        print(result.final_portfolio)

        if result.risk_decisions:
            blocked = sum(len(d.rejected_orders) for d in result.risk_decisions)
            print(f"Risk manager evaluated {len(result.risk_decisions)} bars.")
            print(f"Orders blocked by risk: {blocked}")

        print(f"Run logs: {log.paths.events_file}")
        return 0

    if args.cmd == "live":
        orch.run_live()
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
