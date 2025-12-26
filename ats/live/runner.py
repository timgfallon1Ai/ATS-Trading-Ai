from __future__ import annotations

import logging
import os
import time
from typing import Dict, Optional

from ats.live.broker import Broker
from ats.live.config import LiveConfig
from ats.live.ibkr_broker import IBKRBroker
from ats.live.market_data import MockMarketData, PolygonMarketData
from ats.live.paper_broker import PaperBroker
from ats.live.strategies.analyst_ensemble import AnalystEnsembleStrategy
from ats.live.strategies.buy_and_hold import BuyAndHoldStrategy
from ats.live.strategy import LiveStrategy
from ats.live.types import Bar

log = logging.getLogger("ats.live.runner")


def _kill_switch_enabled() -> bool:
    # Prefer the global kill switch if present.
    try:
        from ats.core.kill_switch import is_kill_switch_enabled  # type: ignore
    except Exception:
        try:
            from ats.backtester2.kill_switch import is_kill_switch_enabled  # type: ignore
        except Exception:
            return False
    try:
        return bool(is_kill_switch_enabled())
    except Exception:
        return False


def _build_market_data(cfg: LiveConfig):
    if cfg.market_data == "mock":
        if not cfg.mock_prices:
            raise ValueError("mock_prices is required when market_data=mock")
        return MockMarketData(cfg.mock_prices)

    if cfg.market_data == "polygon":
        api_key = os.getenv("POLYGON_API_KEY", "")
        return PolygonMarketData(api_key=api_key)

    raise ValueError(f"Unknown market_data: {cfg.market_data}")


def _build_broker(cfg: LiveConfig) -> Broker:
    if cfg.broker == "paper":
        return PaperBroker()

    if cfg.broker == "ibkr":
        host = os.getenv("IBKR_HOST", "127.0.0.1")
        port = int(os.getenv("IBKR_PORT", "7497"))
        client_id = int(os.getenv("IBKR_CLIENT_ID", "7"))
        return IBKRBroker(host=host, port=port, client_id=client_id)

    raise ValueError(f"Unknown broker: {cfg.broker}")


def _build_strategy(cfg: LiveConfig) -> LiveStrategy:
    if cfg.strategy == "buy_and_hold":
        return BuyAndHoldStrategy(
            notional_per_symbol=cfg.notional_per_symbol,
            allow_fractional=cfg.allow_fractional,
        )

    if cfg.strategy == "analyst_ensemble":
        return AnalystEnsembleStrategy(
            notional_per_symbol=cfg.notional_per_symbol,
            allow_fractional=cfg.allow_fractional,
            history_bars=cfg.history_bars,
            warmup_bars=cfg.warmup_bars,
            min_confidence=cfg.min_confidence,
            allow_short=cfg.allow_short,
            rebalance_threshold_notional=cfg.rebalance_threshold_notional,
            log_signals=cfg.log_signals,
        )

    raise ValueError(f"Unknown strategy: {cfg.strategy}")


def run_live(cfg: LiveConfig) -> Broker:
    """Run the live loop. Returns broker instance (useful for tests)."""
    md = _build_market_data(cfg)
    broker = _build_broker(cfg)
    strat = _build_strategy(cfg)

    log.info(
        "LIVE START tag=%s strategy=%s market_data=%s broker=%s symbols=%s execute=%s poll=%.2fs max_ticks=%s",
        cfg.run_tag,
        cfg.strategy,
        cfg.market_data,
        cfg.broker,
        ",".join(cfg.symbols),
        cfg.execute,
        cfg.poll_seconds,
        str(cfg.max_ticks),
    )

    tick = 0
    try:
        while True:
            if cfg.max_ticks is not None and tick >= int(cfg.max_ticks):
                log.info("Reached max_ticks=%s; stopping.", cfg.max_ticks)
                break

            if _kill_switch_enabled():
                log.error("KILL SWITCH ENABLED. Stopping live loop.")
                if cfg.flatten_on_kill:
                    # Best effort flatten using latest prices (if we can fetch them).
                    try:
                        bars = md.get_bars(cfg.symbols)
                        prices = {s: float(b.close) for s, b in bars.items()}
                        broker.flatten(prices=prices, symbols=cfg.symbols)
                    except Exception:
                        log.exception("Flatten on kill failed (best effort).")
                break

            bars: Dict[str, Bar] = md.get_bars(cfg.symbols)

            orders = strat.on_tick(bars, broker)
            if orders:
                log.info("Generated %d orders", len(orders))

            if cfg.execute:
                for o in orders:
                    sym = str(o.symbol).upper()
                    px = float(bars[sym].close) if sym in bars else None
                    broker.place_order(o, price=px)
            else:
                for o in orders:
                    log.info("DRY-RUN order: %s", o)

            tick += 1
            if cfg.poll_seconds > 0:
                time.sleep(float(cfg.poll_seconds))

    finally:
        try:
            md.close()
        except Exception:
            pass
        try:
            broker.close()
        except Exception:
            pass

    return broker
