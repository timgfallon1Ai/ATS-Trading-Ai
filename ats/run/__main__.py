from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Sequence

from ats.run.orchestrator import BacktestRunConfig, RuntimeOrchestrator


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m ats.run",
        description="ATS runtime entrypoint (Phase 14): run backtests and write run artifacts.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    bt = sub.add_parser("backtest", help="Run a backtest and write run artifacts.")
    bt.add_argument("--symbol", required=True, help="Symbol to backtest (e.g., AAPL).")
    bt.add_argument(
        "--days", type=int, default=50, help="Number of bars (default: 50)."
    )
    bt.add_argument("--strategy", default="ma", help="Strategy name (default: ma).")
    bt.add_argument(
        "--strategies",
        default=None,
        help="Comma-separated strategy list (for ensemble-style strategies).",
    )
    bt.add_argument(
        "--max-position-frac",
        type=float,
        default=0.20,
        help="Max position fraction for risk manager (default: 0.20).",
    )
    bt.add_argument("--csv", default=None, help="Optional path to OHLCV CSV.")
    bt.add_argument(
        "--log-dir", type=Path, default=Path("logs"), help="Root log directory."
    )
    bt.add_argument(
        "--run-id", default=None, help="Optional run id (default: auto-generated)."
    )
    bt.add_argument("--no-risk", action="store_true", help="Disable risk manager.")

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "backtest":
        cfg = BacktestRunConfig(
            symbol=str(args.symbol).upper(),
            days=int(args.days),
            strategy=str(args.strategy),
            strategy_names=(
                [p.strip() for p in str(args.strategies).split(",") if p.strip()]
                if args.strategies
                else None
            ),
            max_position_frac=float(args.max_position_frac),
            csv=str(args.csv) if args.csv else None,
            enable_risk=not bool(args.no_risk),
            log_dir=Path(args.log_dir),
            run_id=str(args.run_id) if args.run_id else None,
        )

        orch = RuntimeOrchestrator(log_dir=cfg.log_dir, run_id=cfg.run_id)
        result = orch.run_backtest(cfg)

        print("Backtest complete.")
        if orch.log is not None:
            # Phase 14 test parses this line and expects a FILE path to events.jsonl
            print(f"Run logs: {orch.log.events_path}")

        # Helpful summary (tests don't require it)
        bars = len(getattr(result, "portfolio_history", []) or [])
        trades = len(getattr(result, "trade_history", []) or [])
        print(f"Bars: {bars}")
        print(f"Trades: {trades}")
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
