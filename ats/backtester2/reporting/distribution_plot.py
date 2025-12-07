from typing import Any, Dict, List

import matplotlib.pyplot as plt


class DistributionPlot:
    @staticmethod
    def build(trades: List[Dict[str, Any]], output_path: str):
        if not trades:
            return

        pnls = [t["pnl"] for t in trades]

        plt.figure(figsize=(10, 5))
        plt.hist(pnls, bins=50, edgecolor="black")
        plt.title("Trade PnL Distribution")
        plt.xlabel("PnL")
        plt.ylabel("Frequency")
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
