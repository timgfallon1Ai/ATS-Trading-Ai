from __future__ import annotations

import argparse
import os
from typing import Any, Optional, Sequence

from ats.core.kill_switch import (
    disable_kill_switch,
    enable_kill_switch,
    kill_switch_status,
)
from ats.run.boot import BootConfig, boot_system
from ats.run.orchestrator import RuntimeOrchestrator


def _parse_csv_list(raw: str | None) -> list[str] | None:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    parts = [p.strip() for p in s.split(",")]
    parts = [p for p in parts if p]
    return parts or None


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ats.run",
        description="ATS unified runtime entrypoint (backtest-first).",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_bt = sub.add_parser(
        "backtest",
        help="Run Backtester2 through the unified runtime wrapper.",
    )
    p_bt.add_argument("--symbol", required=True)
    p_bt.add_argument("--days", type=int, default=200)
    p_bt.add_argument(
        "--no-risk",
        action="store_true",
        help="Disable risk manager (Backtester2)",
    )

    # Backtester2 passthroughs
    p_bt.add_argument(
        "--strategy",
        default="ma",
        help="Backtester2 strategy key (e.g. ma, ensemble).",
    )
    p_bt.add_argument(
        "--strategies",
        default=None,
        help="Comma-separated ensemble analyst list (only used if strategy=ensemble).",
    )
    p_bt.add_argument(
        "--max-position-frac",
        type=float,
        default=0.2,
        help="Backtester2 max position fraction per symbol (0..1).",
    )
    p_bt.add_argument(
        "--csv",
        default=None,
        help="Optional CSV bars file to use as data source.",
    )

    # Runtime logging
    p_bt.add_argument("--log-dir", default="logs", help="Base directory for JSONL logs")
    p_bt.add_argument("--run-id", default=None, help="Optional run id (else generated)")
    p_bt.add_argument(
        "--kill-file",
        default=None,
        help="Override kill switch file path",
    )

    p_kill = sub.add_parser("kill", help="Kill-switch controls (file based).")
    kill_sub = p_kill.add_subparsers(dest="kill_cmd", required=True)

    p_kill_status = kill_sub.add_parser("status", help="Show kill switch status")
    p_kill_status.add_argument(
        "--log-dir",
        default="logs",
        help="Base directory for JSONL logs (and kill switch file)",
    )
    p_kill_status.add_argument(
        "--kill-file",
        default=None,
        help="Override kill switch file path",
    )

    p_kill_enable = kill_sub.add_parser("enable", help="Engage kill switch")
    p_kill_enable.add_argument("--reason", default="manual")
    p_kill_enable.add_argument(
        "--log-dir",
        default="logs",
        help="Base directory for JSONL logs (and kill switch file)",
    )
    p_kill_enable.add_argument(
        "--kill-file",
        default=None,
        help="Override kill switch file path",
    )

    p_kill_disable = kill_sub.add_parser("disable", help="Disengage kill switch")
    p_kill_disable.add_argument(
        "--log-dir",
        default="logs",
        help="Base directory for JSONL logs (and kill switch file)",
    )
    p_kill_disable.add_argument(
        "--kill-file",
        default=None,
        help="Override kill switch file path",
    )

    return p


def _status_to_dict(st: Any) -> dict:
    if st is None:
        return {}
    if isinstance(st, dict):
        return st
    to_dict = getattr(st, "to_dict", None)
    if callable(to_dict):
        try:
            v = to_dict()
            if isinstance(v, dict):
                return v
        except Exception:
            pass
    if hasattr(st, "__dict__"):
        try:
            return dict(st.__dict__)
        except Exception:
            pass
    return {"value": str(st)}


def _count_blocked_orders(risk_decisions: Any) -> int:
    if not risk_decisions:
        return 0
    blocked = 0
    for d in risk_decisions:
        if isinstance(d, dict):
            blocked += len(d.get("rejected_orders", []) or [])
        else:
            blocked += len(getattr(d, "rejected_orders", []) or [])
    return blocked


def _print_run_logs_hint(args: Any, reg: Any) -> None:
    """Print the concrete JSONL log path for this run.

    The pipeline test accepts either:
      - a directory containing events.jsonl, or
      - the events.jsonl file itself.

    We prefer the LogWriter instance because it knows the generated run_id.
    """
    # Prefer the LogWriter service registered at boot ("log")
    try:
        log = reg["log"]  # type: ignore[index]
        lp = (
            getattr(log, "path", None)
            or getattr(log, "events_path", None)
            or getattr(log, "log_dir", None)
        )
        if lp:
            print(f"Run logs: {lp}")
            return
    except Exception:
        pass

    # Fallbacks (older registry implementations)
    lp = getattr(reg, "log_path", None) or getattr(reg, "run_log_path", None)
    if lp:
        print(f"Run logs: {lp}")
        return

    base = os.getenv("ATS_LOG_DIR", getattr(args, "log_dir", "logs"))
    rid = os.getenv("ATS_RUN_ID", getattr(args, "run_id", "") or "")
    if rid:
        print(f"Run logs: {base}/{rid}/events.jsonl")
    else:
        print(f"Run logs: {base}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(list(argv) if argv is not None else None)

    # Ensure kill-switch uses the same path conventions as the rest of the system
    if getattr(args, "log_dir", None):
        os.environ["ATS_LOG_DIR"] = str(args.log_dir)
    if getattr(args, "kill_file", None):
        os.environ["ATS_KILL_SWITCH_FILE"] = str(args.kill_file)

    if args.cmd == "kill":
        if getattr(args, "log_dir", None):
            os.environ["ATS_LOG_DIR"] = str(args.log_dir)
        if getattr(args, "kill_file", None):
            os.environ["ATS_KILL_SWITCH_FILE"] = str(args.kill_file)

        if args.kill_cmd == "status":
            st = kill_switch_status()
            d = _status_to_dict(st)
            engaged = d.get("engaged", d.get("is_engaged", False))
            print(f"Kill switch engaged: {bool(engaged)}")
            if "path" in d:
                print(f"Path: {d.get('path')}")
            if "forced_by_env" in d:
                print(f"Forced by env: {bool(d.get('forced_by_env'))}")
            if "file_exists" in d:
                print(f"File exists: {bool(d.get('file_exists'))}")
            if d.get("reason") is not None:
                print(f"Reason: {d.get('reason')}")
            return 0

        if args.kill_cmd == "enable":
            enable_kill_switch(reason=str(args.reason))
            print("Kill switch enabled.")
            return 0

        if args.kill_cmd == "disable":
            disable_kill_switch()
            print("Kill switch disabled.")
            return 0

        raise SystemExit(f"Unknown kill subcommand: {args.kill_cmd}")

    if args.cmd == "backtest":
        reg = boot_system(BootConfig(log_dir=args.log_dir, run_id=args.run_id))

        # Robustly fetch orchestrator; fallback if registry didn’t register it.
        try:
            orch = reg["orchestrator"]  # type: ignore[index]
        except Exception:
            try:
                log = reg["log_writer"]  # type: ignore[index]
            except Exception:
                log = reg["log"]  # type: ignore[index]
            orch = RuntimeOrchestrator(log)  # type: ignore[arg-type]
            try:
                reg["orchestrator"] = orch  # type: ignore[index]
            except Exception:
                pass

        cfg = orch.BacktestRunConfig(
            symbol=str(args.symbol),
            days=int(args.days),
            enable_risk=not bool(args.no_risk),
            csv=str(args.csv) if args.csv else None,
            strategy=str(args.strategy),
            strategy_names=_parse_csv_list(args.strategies),
            max_position_frac=float(args.max_position_frac),
        )

        res = orch.run_backtest(cfg)

        print("Backtest complete.")
        print(f"Trades executed: {len(res.trade_history)}")
        print("Final portfolio snapshot:")
        print(res.final_portfolio)

        if isinstance(res.final_portfolio, dict):
            print(f"Risk manager evaluated {len(res.risk_decisions)} bars.")
            print(
                f"Orders blocked by risk: {_count_blocked_orders(res.risk_decisions)}"
            )

        _print_run_logs_hint(args, reg)
        return 0

    raise SystemExit(f"Unknown command: {args.cmd}")


if __name__ == "__main__":
    raise SystemExit(main())
