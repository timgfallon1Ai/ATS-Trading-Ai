import json
from typing import Any, Dict


class HTMLReport:
    @staticmethod
    def build(output_path: str, analytics: Dict[str, Any]):
        html = f"""
        <html>
        <head>
            <title>Backtest Report</title>
            <style>
                body {{ font-family: Arial; padding: 20px; }}
                h1, h2 {{ margin-bottom: 10px; }}
                pre {{ background: #f4f4f4; padding: 10px; }}
                .section {{ margin-bottom: 30px; }}
            </style>
        </head>
        <body>
            <h1>Backtest Report</h1>

            <div class="section">
                <h2>Portfolio Statistics</h2>
                <pre>{json.dumps(analytics["portfolio_stats"], indent=4)}</pre>
            </div>

            <div class="section">
                <h2>Trade Statistics</h2>
                <pre>{json.dumps(analytics["trade_stats"], indent=4)}</pre>
            </div>

            <div class="section">
                <h2>Attribution by Symbol</h2>
                <pre>{json.dumps(analytics["attribution_symbol"], indent=4)}</pre>
            </div>
        </body>
        </html>
        """

        with open(output_path, "w") as f:
            f.write(html)
