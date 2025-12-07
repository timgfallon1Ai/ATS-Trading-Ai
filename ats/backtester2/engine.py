# ats/backtester2/engine.py

from __future__ import annotations

from typing import Any, Dict, List

from .bt_debug_snapshot import SnapshotRecorder
from .bt_reporter import generate_report
from .bt_trace import BTTrace


class BT2Engine:
    """Full multi-symbol backtest engine (BT-2A).
    Dispatcher-driven modular pipeline.
    """

    def __init__(
        self,
        dispatcher,
        initial_equity: float = 1000.0,
        trace_enabled: bool = False,
        snapshot_enabled: bool = False,
    ):
        self.dispatcher = dispatcher
        self.initial_equity = initial_equity

        self.trace = BTTrace(enabled=trace_enabled)
        self.snapshots = SnapshotRecorder(enabled=snapshot_enabled)

        # Portfolio state (per-symbol qty)
        self.positions: Dict[str, float] = {}
        self.cash: float = initial_equity

        # Logs
        self.trade_log: List[Dict[str, Any]] = []
        self.equity_curve: List[float] = []
        self.pnl_series: List[float] = []
        self.turnover_series: List[float] = []
        self.exposure_series: List[float] = []

    # ---------------------------------------------------------------------
    # Utility
    # ---------------------------------------------------------------------
    def _calc_equity(self, ts: int, bars: Dict[str, Dict[str, float]]) -> float:
        eq = self.cash
        for sym, qty in self.positions.items():
            if sym in bars:
                eq += qty * bars[sym]["close"]
        return eq

    # ---------------------------------------------------------------------
    # Main run loop
    # ---------------------------------------------------------------------
    def run(self, data: Dict[int, Dict[str, Dict[str, float]]]) -> Dict[str, Any]:
        """data: { ts → { symbol → bar } }"""
        for ts, symbol_bars in data.items():
            # ============================
            # 1) Snapshot (pre-bar)
            # ============================
            self.snapshots.record(
                ts, "pre_bar", {"positions": dict(self.positions), "cash": self.cash}
            )

            # ============================
            # 2) Feature extraction
            # ============================
            feats = self.dispatcher.run_features(ts, symbol_bars)
            self.trace.log(ts, "features", feats)

            self.snapshots.record(ts, "features", feats)

            # ============================
            # 3) Strategy signals
            # ============================
            signals = self.dispatcher.run_signals(ts, feats)
            self.trace.log(ts, "signals", signals)

            self.snapshots.record(ts, "signals", signals)

            # ============================
            # 4) Risk manager (RM-4 posture)
            # ============================
            posture = self.dispatcher.run_risk(ts, signals)
            self.trace.log(ts, "posture", posture)

            self.snapshots.record(ts, "posture", posture)

            # ============================
            # 5) Position sizing
            # ============================
            weights = self.dispatcher.size_positions(ts, posture)
            self.trace.log(ts, "weights", weights)

            self.snapshots.record(ts, "weights", weights)

            # ============================
            # 6) Convert weights → target qty
            # ============================
            targets = {}
            eq = self._calc_equity(ts, symbol_bars)
            for sym, w in weights.items():
                if sym not in symbol_bars:
                    continue
                px = symbol_bars[sym]["close"]
                targets[sym] = (eq * w) / px if px > 0 else 0.0

            self.trace.log(ts, "targets", targets)
            self.snapshots.record(ts, "targets", targets)

            # ============================
            # 7) Generate trades (delta between positions)
            # ============================
            bar_trades = {}
            turnover_amt = 0.0

            for sym, tgt_qty in targets.items():
                cur_qty = self.positions.get(sym, 0.0)
                delta = tgt_qty - cur_qty
                if abs(delta) > 1e-9:
                    bar_trades[sym] = delta
                    turnover_amt += abs(delta)

            self.trace.log(ts, "trades", bar_trades)

            # ============================
            # 8) Apply trades
            # ============================
            for sym, qty_delta in bar_trades.items():
                px = symbol_bars[sym]["close"]
                cost = qty_delta * px

                # buy reduces cash / sell increases cash
                self.cash -= cost

                # update positions
                self.positions[sym] = self.positions.get(sym, 0.0) + qty_delta

                # trade log entry
                self.trade_log.append(
                    {
                        "ts": ts,
                        "symbol": sym,
                        "qty": qty_delta,
                        "price": px,
                        "cost": cost,
                    }
                )

            # ============================
            # 9) End of bar equity
            # ============================
            eq_end = self._calc_equity(ts, symbol_bars)
            pnl = eq_end - (
                self.equity_curve[-1] if self.equity_curve else self.initial_equity
            )

            self.equity_curve.append(eq_end)
            self.pnl_series.append(pnl)
            self.turnover_series.append(turnover_amt)
            self.exposure_series.append(
                sum(
                    abs(q) * symbol_bars[sym]["close"]
                    for sym, q in self.positions.items()
                )
            )

            self.trace.log(
                ts,
                "equity",
                {
                    "equity": eq_end,
                    "pnl": pnl,
                    "cash": self.cash,
                    "positions": dict(self.positions),
                },
            )

            self.snapshots.record(
                ts,
                "post_bar",
                {
                    "equity": eq_end,
                    "pnl": pnl,
                    "cash": self.cash,
                    "positions": dict(self.positions),
                },
            )

        # =====================================================
        # Final backtest report
        # =====================================================
        per_symbol_returns = {sym: (self.positions[sym] * 0) for sym in self.positions}

        return generate_report(
            equity_curve=self.equity_curve,
            pnl_series=self.pnl_series,
            trades=self.trade_log,
            per_symbol_returns=per_symbol_returns,
            exposure_series=self.exposure_series,
            turnover_series=self.turnover_series,
        )
