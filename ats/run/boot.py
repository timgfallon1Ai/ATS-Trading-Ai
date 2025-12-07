from __future__ import annotations

from typing import List

from run.service_registry import ServiceRegistry
from run.system_clock import SystemClock

from ats.aggregator.live_aggregator_engine import LiveAggregatorEngine
from ats.analyst.analyst_engine import AnalystEngine
from ats.dashboard.server import DashboardFeed

# Subsystems
from ats.data_ingestion.ubf_ingestor import UBFIngestor
from ats.live_risk.posture_sync import PostureSync
from ats.risk_manager.risk_manager import RiskManager
from ats.trader_live.latency_model import LatencyModel
from ats.trader_live.live_execution_engine import LiveExecutionEngine
from ats.trader_live.live_market_data import LiveMarketData
from ats.trader_live.live_order_router import LiveOrderRouter
from ats.trader_live.live_position_book import LivePositionBook
from ats.trader_live.order_converter import OrderConverter
from ats.trader_live.portfolio_equity import PortfolioEquity
from ats.trader_live.slippage_model import SlippageModel
from ats.trader_live.trade_loop import TradeLoop


def boot_system(symbols: List[str]):
    """E2E boot: wiring all ATS subsystems together."""
    reg = ServiceRegistry({})

    # -----------------------------
    # 1) INGESTION
    # -----------------------------
    reg.add("ubf", UBFIngestor(symbols))

    # -----------------------------
    # 2) ANALYST
    # -----------------------------
    reg.add("analyst", AnalystEngine(symbols))

    # -----------------------------
    # 3) RISK MANAGER
    # -----------------------------
    reg.add("risk", RiskManager())

    # -----------------------------
    # 4) AGGREGATOR
    # -----------------------------
    reg.add("aggregator", LiveAggregatorEngine())

    # -----------------------------
    # 5) TRADER
    # -----------------------------
    md = LiveMarketData(fetch_fn=lambda s: reg["ubf"].fetch_symbol(s))
    book = LivePositionBook()
    equity = PortfolioEquity(1000.0)
    equity.attach_book(book)

    exec_engine = LiveExecutionEngine(
        latency=LatencyModel(),
        slippage=SlippageModel(),
    )

    order_router = LiveOrderRouter(route_fn=lambda o: o)

    trader = TradeLoop(
        symbols=symbols,
        analyst_fn=lambda barset: reg["analyst"].generate_multi(barset),
        aggregator=reg["aggregator"],
        md=md,
        execution=exec_engine,
        router=order_router,
        converter=OrderConverter(),
        book=book,
        equity=equity,
        posture=PostureSync(),
    )

    reg.add("trader", trader)
    reg.add("equity", equity)
    reg.add("book", book)
    reg.add("posture", PostureSync())

    # -----------------------------
    # 6) DASHBOARD
    # -----------------------------
    reg.add("dashboard", DashboardFeed())

    # -----------------------------
    # 7) CLOCK
    # -----------------------------
    reg.add("clock", SystemClock(interval=1.0))

    return reg
