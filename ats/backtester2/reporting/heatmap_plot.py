from typing import Dict

import matplotlib.pyplot as plt
import seaborn as sns


class HeatmapPlot:
    @staticmethod
    def build(symbol_attrib: Dict[str, float], output_path: str):
        if not symbol_attrib:
            return

        symbols = list(symbol_attrib.keys())
        values = list(symbol_attrib.values())

        plt.figure(figsize=(8, 4))
        sns.heatmap(
            [values], annot=True, fmt=".2f", xticklabels=symbols, yticklabels=["PnL"]
        )
        plt.title("Symbol-Level PnL Heatmap")
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
