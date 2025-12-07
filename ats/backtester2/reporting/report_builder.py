import os
from typing import Any, Dict, List

from ats.backtester2.reporting.csv_exporter import CSVExporter
from ats.backtester2.reporting.distribution_plot import DistributionPlot
from ats.backtester2.reporting.equity_plot import EquityPlot
from ats.backtester2.reporting.heatmap_plot import HeatmapPlot
from ats.backtester2.reporting.html_report import HTMLReport
from ats.backtester2.reporting.trade_plot import TradePlot


class ReportBuilder:
    """High-level orchestrator for generating all reports."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def build(self, equity_curve: List[Dict[str, Any]], analytics: Dict[str, Any]):

        # ---- 1. Plots ----
        EquityPlot.build(equity_curve, f"{self.output_dir}/equity.png")
        TradePlot.build(analytics["trades"], f"{self.output_dir}/trades.png")
        DistributionPlot.build(
            analytics["trades"], f"{self.output_dir}/distribution.png"
        )
        HeatmapPlot.build(
            analytics["attribution_symbol"], f"{self.output_dir}/heatmap.png"
        )

        # ---- 2. CSV Exports ----
        CSVExporter.write_dicts(f"{self.output_dir}/trades.csv", analytics["trades"])
        CSVExporter.write_stats(
            f"{self.output_dir}/portfolio_stats.csv", analytics["portfolio_stats"]
        )
        CSVExporter.write_stats(
            f"{self.output_dir}/trade_stats.csv", analytics["trade_stats"]
        )

        # ---- 3. HTML Report ----
        HTMLReport.build(f"{self.output_dir}/report.html", analytics)
