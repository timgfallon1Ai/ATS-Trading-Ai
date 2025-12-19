from __future__ import annotations

import argparse
from typing import Optional, Sequence

from ats.run.boot import BootConfig, boot_system
from ats.run.orchestrator import BacktestRequest


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ats.run",
        description="ATS unified runtime entrypoint (backtest-first).",
    )

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_bt = sub.add_parser(
        "backtest",
        help="Run Backtester2 (synthetic bars) through the unified runtime wrapper.",
    )
    p_bt.add_argument("--symbol", required=True, help="Symbol to backtest (e.g. AAPL).")
    p_bt.add_argument(
        "--days",
        type=int,
        default=200,
        help="Number of synthetic daily bars to generate (default: 200).",
    )
    p_bt.add_argument(
        "--starting-cash",
        type=float,
        default=100000.0,
        help="Starting cash for the portfolio (default: 100000).",
    )
    p_bt.add_argument(
        "--no-risk",
        action="store_true",
        help="Disable the RiskManager path (for debugging / parity checks).",
    )
    p_bt.add_argument(
        "--log-dir",
        default="logs",
        help="Directory for JSONL logs (default: logs).",
    )
    p_bt.add_argument(
        "--run-id",
        default=None,
        help="Optional run id for log correlation (default: auto-generated).",
    )
    p_bt.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress human-friendly console output (still writes logs).",
    )

    p_live = sub.add_parser(
        "live",
        help="Placeholder for future live/paper trading loop (not implemented yet).",
    )
    p_live.add_argument(
        "--log-dir",
        default="logs",
        help="Directory for JSONL logs (default: logs).",
    )
    p_live.add_argument(
        "--run-id",
        default=None,
        help="Optional run id for log correlation (default: auto-generated).",
    )

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.cmd == "backtest":
        reg = boot_system(BootConfig(log_dir=args.log_dir, run_id=args.run_id))
        orch = reg["orchestrator"]

        req = BacktestRequest(
            symbol=str(args.symbol),
            days=int(args.days),
            starting_cash=float(args.starting_cash),
            no_risk=bool(args.no_risk),
        )
        result = orch.run_backtest(req)

        if not args.quiet:
            trade_history = getattr(result, "trade_history", None)
            if trade_history is None:
                trade_history = getattr(result, "trades", None)

            final_portfolio = getattr(result, "final_portfolio", None)
            if final_portfolio is None:
                final_portfolio = getattr(result, "portfolio", None)

            print("Backtest complete.")
            if isinstance(trade_history, list):
                print(f"Trades executed: {len(trade_history)}")
            else:
                print("Trades executed: (unknown)")

            if final_portfolio is not None:
                print("Final portfolio snapshot:")
                print(final_portfolio)
            else:
                print("No final portfolio snapshot available.")

            print(f"Run id: {orch.run_id}")
            print(f"Logs: {args.log_dir}")

        return 0

    if args.cmd == "live":
        reg = boot_system(BootConfig(log_dir=args.log_dir, run_id=args.run_id))
        orch = reg["orchestrator"]
        raise SystemExit(
            f"Live mode is not implemented yet. (run_id={orch.run_id}, logs={args.log_dir})"
        )

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
