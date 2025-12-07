from typing import Any, Dict, List

import matplotlib.pyplot as plt


class EquityPlot:
    @staticmethod
    def build(equity_curve: List[Dict[str, Any]], output_path: str):
        timestamps = [row["timestamp"] for row in equity_curve]
        values = [row["equity"] for row in equity_curve]

        plt.figure(figsize=(12, 5))
        plt.plot(timestamps, values)
        plt.title("Equity Curve")
        plt.xlabel("Timestamp")
        plt.ylabel("Equity ($)")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
