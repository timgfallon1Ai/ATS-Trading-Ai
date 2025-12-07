import csv
from typing import Any, Dict, List


class CSVExporter:

    @staticmethod
    def write_dicts(path: str, rows: List[Dict[str, Any]]):
        if not rows:
            return

        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    @staticmethod
    def write_stats(path: str, stats: Dict[str, Any]):
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            for k, v in stats.items():
                writer.writerow([k, v])
