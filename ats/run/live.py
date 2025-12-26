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
            "symbols must be comma-separated, e.g. AAPL,MSFT"
        )
    return syms


def _parse_mock_prices(raw: str) -> Dict[str, float]:
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

    p.add_argument("--symbols", type=_parse_symbols, default=["AAPL"])
    p.add_argument("--market-data", choices=["polygon", "mock"], default="polygon")
    p.add_argument(
        "--mock-prices",
        type=_parse_mock_prices,
        default=_parse_mock_prices(os.getenv("ATS_MOCK_PRICES", "")),
        help="mock only: AAA=10,BBB=20 (or ATS_MOCK_PRICES)",
    )
    p.add_argument("--broker", choices=["paper", "ibkr"], default="paper")
    p.add_argument("--poll-seconds", type=float, default=5.0)
    p.add_argument("--max-ticks", type=int, default=None)

    p.add_argument("--execute", action="store_true")
    p.add_argument("--allow-live", action="store_true")
    p.add_argument("--no-flatten-on-kill", action="store_true")

    p.add_argument(
        "--strategy",
        choices=["buy_and_hold", "analyst_ensemble"],
        default="buy_and_hold",
    )
    p.add_argument("--notional-per-symbol", type=float, default=100.0)
    p.add_argument("--allow-fractional", action="store_true")

    # Analyst ensemble knobs
    p.add_argument("--history-bars", type=int, default=120)
    p.add_argument("--warmup-bars", type=int, default=30)
    p.add_argument("--min-confidence", type=float, default=0.15)
    p.add_argument("--allow-short", action="store_true")
    p.add_argument("--rebalance-threshold-notional", type=float, default=5.0)
    p.add_argument("--log-signals", action="store_true")

    p.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=os.getenv("ATS_LOG_LEVEL", "INFO"),
    )
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, str(args.log_level)),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # Safety gate: if using a non-paper broker and executing, require explicit allow-live.
    if args.execute and args.broker != "paper" and not args.allow_live:
        print(
            f"Refusing to execute with broker='{args.broker}' without --allow-live.\n"
            "Use --allow-live ONLY after verifying you are on a PAPER account and you understand the risks.",
            file=sys.stderr,
        )
        return 2

    if args.market_data == "mock":
        missing = [s for s in args.symbols if s not in args.mock_prices]
        if missing:
            print("Missing --mock-prices for: %s" % ", ".join(missing), file=sys.stderr)
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
        history_bars=int(args.history_bars),
        warmup_bars=int(args.warmup_bars),
        min_confidence=float(args.min_confidence),
        allow_short=bool(args.allow_short),
        rebalance_threshold_notional=float(args.rebalance_threshold_notional),
        log_signals=bool(args.log_signals),
        run_tag="phase15.2",
    )

    run_live(cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
