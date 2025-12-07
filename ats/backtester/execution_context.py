# ats/backtester/execution_context.py

from typing import Dict, Any

class ExecutionContext:
    """
    Holds persistent state for the backtest:
    - Analyst engine
    - Aggregator
    - RM-MASTER
    - Trader
    - Portfolio state
    """

    def __init__(self, analyst, aggregator, rm_master, trader):
        self.analyst = analyst
        self.aggregator = aggregator
        self.rm_master = rm_master
        self.trader = trader

        self.portfolio_history = []
        self.trade_history = []
        self.rm_packets = []
        self.allocations = []
        self.signals = []

    def snapshot(self, portfolio_state):
        self.portfolio_history.append(portfolio_state)
