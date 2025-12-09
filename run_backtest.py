#!/usr/bin/env python3
"""
Z-13 BACKTEST ENTRYPOINT

Run a full ATS backtest using:
- Polygon OHLCV 1-minute bars
- Benzinga news
- 12-strategy Hybrid Analyst (MM-2)
- Aggregator (Hybrid Universe)
- RM-MASTER (Unified Risk Manager)
- T1 Trader (Dollar→Shares Execution)
"""

from __future__ import annotations
import os
import yaml
import pandas as pd

# ------------------------------
# ATS Imports
# ------------------------------
from ats.market_gateway.gateway import MarketGateway
from ats.analyst.hybrid_analyst import HybridAnalyst
from ats.aggregator.aggregator import Aggregator
from ats.risk_manager.risk_manager import RiskManager
from ats.trader.trader import Trader

from ats.backtester.backtester import Backtester
from ats.backtester.data_loader_polygon import PolygonDataLoader
from ats.backtester.data_loader_benzinga import BenzingaNewsLoader


# ============================================================
# LOAD CONFIG FILE
# ============================================================
def load_keys():
    with open("keys.yaml", "r") as f:
        return yaml.safe_load(f)


# ============================================================
# MAIN BACKTEST RUNNER
# ============================================================
def main():
    print("🔄 Loading config…")
    keys = load_keys()

    polygon_key = keys["polygon"]["api_key"]
    benzinga_key = keys["benzinga"]["api_key"]

    # ========================================================
    # USER SETTINGS — CHANGE THESE AS YOU LIKE
    # ========================================================
    SYMBOL = "AAPL"
    START = "2023-01-03"
    END = "2023-01-10"

    print(f"📊 Loading historical bars for {SYMBOL}…")
    poly = PolygonDataLoader(api_key=polygon_key)
    bars_df = poly.load(SYMBOL, START, END)

    print(f"📰 Loading Benzinga news for {SYMBOL}…")
    bz = BenzingaNewsLoader(api_key=benzinga_key)
    news_events = bz.load(SYMBOL, START, END)

    # ========================================================
    # CONSTRUCT ATS PIPELINE OBJECTS
    # ========================================================
    print("🧠 Initializing Hybrid Analyst engine…")
    analyst = HybridAnalyst()

    print("📦 Initializing Aggregator…")
    aggregator = Aggregator()

    print("🛡️ Initializing RM-MASTER (Unified Risk Manager)…")
    rm_master = RiskManager()

    print("🤖 Initializing Trader (T1)…")
    trader = Trader(starting_capital=1000.0)

    print("🧪 Initializing Backtester…")
    bt = Backtester(
        analyst=analyst,
        aggregator=aggregator,
        rm_master=rm_master,
        trader=trader,
    )

    bt.load_data(bars_df, news_events)

    # ========================================================
    # RUN BACKTEST
    # ========================================================
    print("🚀 Running simulation…")
    results = bt.run()

    # ========================================================
    # SAVE OUTPUT
    # ========================================================
    os.makedirs("backtest_output", exist_ok=True)

    print("💾 Writing results → backtest_output/")
    pd.DataFrame(results["portfolio"]).to_csv(
        "backtest_output/portfolio.csv", index=False
    )
    pd.DataFrame(results["trades"]).to_csv("backtest_output/trades.csv", index=False)

    # RM packets are nested dicts → save JSON
    import json

    with open("backtest_output/rm_packets.json", "w") as f:
        json.dump(results["rm_packets"], f, indent=2)

    print("✅ Backtest complete!")


if __name__ == "__main__":
    main()
