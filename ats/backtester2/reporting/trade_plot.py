from typing import Any, Dict, List

import matplotlib.pyplot as plt


class TradePlot:
    @staticmethod
    def build(trades: List[Dict[str, Any]], output_path: str):
        if not trades:
            return

        entry_ts = [t["entry_timestamp"] for t in trades]
        exit_ts = [t["exit_timestamp"] for t in trades]
        pnl = [t["pnl"] for t in trades]

        plt.figure(figsize=(12, 5))
        colors = ["green" if p > 0 else "red" for p in pnl]

        for i in range(len(trades)):
            plt.plot([entry_ts[i], exit_ts[i]], [0, pnl[i]], color=colors[i])

        plt.title("Trade Lifecycle Overview")
        plt.xlabel("Timestamp")
        plt.ylabel("PnL")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
