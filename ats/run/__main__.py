from __future__ import annotations

import argparse
import os
from typing import Sequence

from ats.core.kill_switch import (
    disable_kill_switch,
    enable_kill_switch,
    read_kill_switch_status,
)
from ats.run.boot import BootConfig, boot_system
from ats.run.orchestrator import BacktestRunConfig


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ats.run",
        description="ATS unified runtime entrypoint (backtest-first).",
    )

    parser.add_argument(
        "--log-dir", default="logs", help="Base directory for run logs (default: logs)."
    )
    parser.add_argument(
        "--run-id", default=None, help="Override run_id (default: auto-generated)."
    )

    # Kill-switch file path override (propagates to engine via env var)
    parser.add_argument(
        "--kill-file",
        default=None,
        help="Override kill-switch file path (default: logs/KILL_SWITCH).",
    )

    sub = parser.add_subparsers(dest="cmd", required=True)

    bt = sub.add_parser(
        "backtest", help="Run Backtester2 through the unified runtime wrapper."
    )
    bt.add_argument("--symbol", required=True, help="Symbol to backtest (e.g. AAPL).")
    bt.add_argument(
        "--days",
        type=int,
        default=200,
        help="Number of synthetic daily bars (default: 200).",
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
        "--symbol", default=None, help="(Reserved) Symbol for the live loop."
    )

    ks = sub.add_parser("kill", help="Manage the file-based kill switch.")
    ks_sub = ks.add_subparsers(dest="kill_cmd", required=True)

    ks_status = ks_sub.add_parser("status", help="Show kill switch status.")
    ks_status.add_argument("--reason", default=None, help="(ignored)")

    ks_on = ks_sub.add_parser("on", help="Enable kill switch (creates the kill file).")
    ks_on.add_argument(
        "--reason", default="manual", help="Reason to write into the kill file."
    )

    ks_off = ks_sub.add_parser(
        "off", help="Disable kill switch (removes the kill file)."
    )
    ks_off.add_argument("--reason", default=None, help="(ignored)")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    # Propagate kill-file override globally so engine checks the same file path.
    if args.kill_file:
        os.environ["ATS_KILL_SWITCH_FILE"] = str(args.kill_file)

    if args.cmd == "kill":
        if args.kill_cmd == "status":
            st = read_kill_switch_status()
            print(f"Kill switch engaged: {st.engaged}")
            print(f"Path: {st.path}")
            print(f"Forced by env: {st.forced_by_env}")
            print(f"File exists: {st.file_exists}")
            if st.enabled_at:
                print(f"Enabled at: {st.enabled_at}")
            if st.reason:
                print(f"Reason: {st.reason}")
            return 0

        if args.kill_cmd == "on":
            p = enable_kill_switch(reason=str(args.reason))
            print(f"Kill switch enabled: {p}")
            return 0

        if args.kill_cmd == "off":
            disable_kill_switch()
            st = read_kill_switch_status()
            print(f"Kill switch engaged: {st.engaged}")
            print(f"Path: {st.path}")
            return 0

        return 2

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
