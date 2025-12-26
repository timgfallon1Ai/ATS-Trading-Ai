"""Phase 15.1 live runner CLI.

This is intentionally separate from `python -m ats.run` until Phase 15.2,
so we can iterate without risking the backtest CLI / tests.

Usage:
  python -m ats.run.live --symbols AAPL,MSFT
  python -m ats.run.live --symbols AAPL --execute --broker paper
  python -m ats.run.live --symbols AAPL --broker ibkr --execute --allow-live

Offline/dev usage (no network):
  python -m ats.run.live --market-data mock --symbols AAA,BBB --mock-prices AAA=10,BBB=20 --execute

Notes:
- Default is DRY-RUN (no orders placed).
- Use paper trading first. Live trading should require explicit opt-in.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Dict, List, Optional

from ats.live.config import LiveConfig
from ats.live.runner import run_live


def _parse_symbols(raw: str) -> List[str]:
    syms = [s.strip().upper() for s in (raw or "").split(",") if s.strip()]
    if not syms:
        raise argparse.ArgumentTypeError(
            "symbols must be a comma-separated list, e.g. AAPL,MSFT"
        )
    return syms


def _parse_mock_prices(raw: str) -> Dict[str, float]:
    """Parse 'AAA=10,BBB=20' into {'AAA': 10.0, 'BBB': 20.0}."""
    out: Dict[str, float] = {}
    raw = (raw or "").strip()
    if not raw:
        return out

    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        if "=" not in item:
            raise argparse.ArgumentTypeError(
                f"Invalid mock price '{item}'. Expected SYMBOL=PRICE."
            )
        sym, px = item.split("=", 1)
        sym = sym.strip().upper()
        try:
            out[sym] = float(px.strip())
        except ValueError as e:
            raise argparse.ArgumentTypeError(f"Invalid price for '{sym}': {px}") from e
    return out


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m ats.run.live", add_help=True)

    p.add_argument(
        "--symbols",
        type=_parse_symbols,
        default=["AAPL"],
        help="Comma-separated symbols to trade (default: AAPL).",
    )
    p.add_argument(
        "--market-data",
        choices=["polygon", "mock"],
        default="polygon",
        help="Market data provider (default: polygon).",
    )
    p.add_argument(
        "--mock-prices",
        type=_parse_mock_prices,
        default=_parse_mock_prices(os.getenv("ATS_MOCK_PRICES", "")),
        help="For --market-data mock only. Format: AAA=10,BBB=20 (or env ATS_MOCK_PRICES).",
    )
    p.add_argument(
        "--broker",
        choices=["paper", "ibkr"],
        default="paper",
        help="Broker adapter (default: paper).",
    )
    p.add_argument(
        "--poll-seconds",
        type=float,
        default=5.0,
        help="Polling interval in seconds (default: 5).",
    )
    p.add_argument(
        "--max-ticks",
        type=int,
        default=None,
        help="Stop after N loop ticks (useful for smoke tests).",
    )
    p.add_argument(
        "--execute",
        action="store_true",
        help="Actually place orders. Default is dry-run (log only).",
    )
    p.add_argument(
        "--allow-live",
        action="store_true",
        help="Explicit opt-in required to place orders on non-paper brokers.",
    )
    p.add_argument(
        "--no-flatten-on-kill",
        action="store_true",
        help="Do NOT attempt to flatten positions when kill switch is engaged.",
    )
    p.add_argument(
        "--strategy",
        choices=["buy_and_hold"],
        default="buy_and_hold",
        help="Strategy to run (default: buy_and_hold).",
    )
    p.add_argument(
        "--notional-per-symbol",
        type=float,
        default=100.0,
        help="Budget per symbol for buy_and_hold (default: 100.0).",
    )
    p.add_argument(
        "--allow-fractional",
        action="store_true",
        help="Allow fractional share sizing (default: disabled).",
    )
    p.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=os.getenv("ATS_LOG_LEVEL", "INFO"),
        help="Log level (default: INFO or ATS_LOG_LEVEL).",
    )
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    logging.getLogger("ats.live").setLevel(getattr(logging, args.log_level))

    # Safety gate: if using a non-paper broker and executing, require explicit allow-live.
    if args.execute and args.broker != "paper" and not args.allow_live:
        print(
            "Refusing to execute with broker='%s' without --allow-live.\n"
            "Run with --allow-live ONLY after verifying you are on a PAPER account and you understand the risks."
            % args.broker,
            file=sys.stderr,
        )
        return 2

    if args.market_data == "mock":
        # Ensure mock prices cover all symbols.
        missing = [s for s in args.symbols if s not in args.mock_prices]
        if missing:
            print(
                "Missing --mock-prices entries for: %s" % ", ".join(missing),
                file=sys.stderr,
            )
            return 2

    cfg = LiveConfig(
        symbols=args.symbols,
        market_data=args.market_data,
        broker=args.broker,
        poll_seconds=float(args.poll_seconds),
        max_ticks=args.max_ticks,
        execute=bool(args.execute),
        flatten_on_kill=not bool(args.no_flatten_on_kill),
        strategy=args.strategy,
        notional_per_symbol=float(args.notional_per_symbol),
        allow_fractional=bool(args.allow_fractional),
        mock_prices=dict(args.mock_prices) if args.market_data == "mock" else None,
        run_tag="phase15.1",
    )

    run_live(cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
