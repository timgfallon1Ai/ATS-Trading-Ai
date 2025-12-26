from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, Optional

from ats.core.kill_switch import kill_switch_engaged

from .broker import Broker
from .config import LiveConfig
from .market_data import MarketDataProvider, PolygonMarketData, StaticMarketData
from .paper_broker import PaperBroker
from .strategies.buy_and_hold import BuyAndHoldStrategy


def _default_logger() -> logging.Logger:
    logger = logging.getLogger("ats.live")
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    if logger.level == logging.NOTSET:
        logger.setLevel(logging.INFO)
    return logger


@dataclass
class LiveRunner:
    config: LiveConfig
    broker: Broker
    market_data: MarketDataProvider
    strategy: object  # Strategy protocol; keep loose to avoid runtime typing deps
    logger: Optional[logging.Logger] = None
    kill_switch_fn: Callable[[], bool] = kill_switch_engaged
    sleep_fn: Callable[[float], None] = time.sleep

    def __post_init__(self) -> None:
        if self.logger is None:
            self.logger = _default_logger()

    @classmethod
    def from_config(cls, config: LiveConfig) -> "LiveRunner":
        # Market data
        if config.market_data == "polygon":
            md: MarketDataProvider = PolygonMarketData()
        elif config.market_data == "mock":
            if not config.mock_prices:
                raise ValueError(
                    "market_data='mock' requires LiveConfig.mock_prices (e.g. {'AAPL': 200.0})."
                )
            md = StaticMarketData(prices=dict(config.mock_prices), source="mock")
        else:
            raise ValueError(f"Unknown market_data provider: {config.market_data}")

        # Broker
        if config.broker == "paper":
            broker: Broker = PaperBroker()
        elif config.broker == "ibkr":
            from .ibkr_broker import IBKRBroker

            broker = IBKRBroker()
        else:
            raise ValueError(f"Unknown broker: {config.broker}")

        # Strategy
        if config.strategy == "buy_and_hold":
            strat = BuyAndHoldStrategy(
                notional_per_symbol=config.notional_per_symbol,
                allow_fractional=config.allow_fractional,
            )
        else:
            raise ValueError(f"Unknown strategy: {config.strategy}")

        return cls(config=config, broker=broker, market_data=md, strategy=strat)

    def run(self) -> None:
        assert self.logger is not None

        self.logger.info(
            "LiveRunner starting (execute=%s, broker=%s, market_data=%s, symbols=%s, poll=%.2fs, max_ticks=%s)",
            self.config.execute,
            self.config.broker,
            self.config.market_data,
            ",".join(self.config.symbols),
            self.config.poll_seconds,
            self.config.max_ticks,
        )

        last_prices: Dict[str, float] = {}
        tick_count = 0

        try:
            while True:
                if self.config.max_ticks is not None and tick_count >= int(
                    self.config.max_ticks
                ):
                    self.logger.info(
                        "Reached max_ticks=%s; stopping.", self.config.max_ticks
                    )
                    break

                if self.kill_switch_fn():
                    self.logger.warning("KILL SWITCH ENGAGED. Stopping live loop.")
                    if self.config.flatten_on_kill and last_prices:
                        ts = datetime.now(tz=timezone.utc)
                        try:
                            fills = self.broker.flatten_all(
                                prices=last_prices, timestamp=ts
                            )
                            if fills:
                                self.logger.warning(
                                    "Flattened %d positions due to kill switch.",
                                    len(fills),
                                )
                        except Exception as e:
                            self.logger.exception("Flatten failed: %s", e)
                    break

                for symbol in self.config.symbols:
                    try:
                        tick = self.market_data.get_last_trade(symbol)
                    except Exception as e:
                        self.logger.warning("Market data error for %s: %s", symbol, e)
                        continue

                    last_prices[symbol] = tick.price

                    state = self.broker.get_state()
                    try:
                        orders = self.strategy.generate_orders(tick, state)  # type: ignore[attr-defined]
                    except Exception as e:
                        self.logger.exception("Strategy error for %s: %s", symbol, e)
                        continue

                    for order in orders:
                        if not self.config.execute:
                            self.logger.info("DRY-RUN order: %s", order)
                            continue
                        try:
                            fill = self.broker.place_order(
                                order, price=tick.price, timestamp=tick.timestamp
                            )
                            self.logger.info("FILL: %s", fill)
                        except Exception as e:
                            self.logger.exception("Order failed (%s): %s", order, e)

                tick_count += 1
                self.sleep_fn(float(self.config.poll_seconds))

        finally:
            try:
                self.broker.close()
            except Exception:
                pass
            self.logger.info("LiveRunner stopped.")


def run_live(config: LiveConfig) -> None:
    """Convenience wrapper."""
    LiveRunner.from_config(config).run()
