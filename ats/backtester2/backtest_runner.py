import time
from typing import Any, Dict, Iterable

from ats.backtester2.context import BacktestContext
from ats.backtester2.live_bindings import LiveBindings
from ats.backtester2.pipeline import BacktestPipeline


class BacktestRunner:
    """Orchestrates full backtests:
    - Creates manifest
    - Calls pipeline for each bar
    - Writes summary metrics at the end
    """

    def __init__(self, ctx: BacktestContext, bindings: LiveBindings):
        self.ctx = ctx
        self.pipeline = BacktestPipeline(ctx, bindings)

    def run(self, bars: Iterable[Dict[str, Any]]) -> None:
        start_ts = None
        end_ts = None
        count = 0

        for bar in bars:
            ts = bar["timestamp"]

            if start_ts is None:
                start_ts = ts
            end_ts = ts

            self.pipeline.process_bar(bar, ts)
            count += 1

        # Final metrics
        metrics = self.ctx.trader.compute_metrics()

        # Save
        self.ctx.results.write(
            {
                "bar_count": count,
                "start_ts": start_ts,
                "end_ts": end_ts,
                "metrics": metrics,
            }
        )

        # Manifest as final lock
        self.ctx.manifest.write(
            {
                "engine_version": "BT-2A",
                "symbols": self.ctx.config.get("symbols", []),
                "bar_count": count,
                "start_ts": start_ts,
                "end_ts": end_ts,
                "timestamp_run": int(time.time()),
                "notes": self.ctx.config.get("notes", ""),
            }
        )
