from __future__ import annotations

import json
from pathlib import Path


def _extract_run_log_path(stdout: str) -> str | None:
    for line in stdout.splitlines():
        if line.strip().startswith("Run logs:"):
            return line.split("Run logs:", 1)[1].strip()
    return None


def test_ats_run_backtest_pipeline_creates_jsonl_logs(run_module, project_root) -> None:
    """
    End-to-end smoke test:
      python -m ats.run backtest --symbol AAPL --days N
    and verify it writes a JSONL log file.
    """
    res = run_module("ats.run", ["backtest", "--symbol", "AAPL", "--days", "50"])
    assert res.returncode == 0, res.output
    assert "Backtest complete" in res.stdout, res.output

    log_path_str = _extract_run_log_path(res.stdout)
    assert log_path_str, "Expected 'Run logs:' line in stdout.\n" + res.stdout

    p = Path(log_path_str)
    if not p.is_absolute():
        p = project_root / p

    # Some implementations might print a directory; others print the JSONL file directly.
    log_file = p / "events.jsonl" if p.is_dir() else p
    assert log_file.exists(), f"Expected log file at: {log_file}\n\n{res.output}"

    lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
    assert lines, f"Log file exists but is empty: {log_file}"

    # Validate first chunk as JSON objects
    for idx, line in enumerate(lines[:50], start=1):
        try:
            obj = json.loads(line)
        except Exception as e:  # noqa: BLE001
            raise AssertionError(
                f"Invalid JSON on line {idx} of {log_file}: {e}\nLine: {line!r}"
            )
        assert isinstance(
            obj, dict
        ), f"Expected JSON object on line {idx}, got {type(obj)}"
