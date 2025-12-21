import subprocess
import sys
from pathlib import Path


def test_backtester2_cli_csv_smoke(tmp_path: Path) -> None:
    csv_path = tmp_path / "AAPL.csv"
    csv_path.write_text(
        "timestamp,open,high,low,close,volume\n"
        "2025-01-01,100,101,99,100.5,1000\n"
        "2025-01-02,100.5,102,100,101.5,1100\n"
        "2025-01-03,101.5,103,101,102.5,1200\n",
        encoding="utf-8",
    )

    cmd = [
        sys.executable,
        "-m",
        "ats.backtester2.run",
        "--symbol",
        "AAPL",
        "--csv",
        str(csv_path),
        "--no-risk",
        "--strategy",
        "ma",
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    assert p.returncode == 0, (p.stdout, p.stderr)
    assert "Backtest complete." in (p.stdout + p.stderr)
    assert "Performance metrics:" in (p.stdout + p.stderr)
