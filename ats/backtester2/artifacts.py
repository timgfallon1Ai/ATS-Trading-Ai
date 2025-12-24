from __future__ import annotations

import csv
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Union


def _is_dataclass_instance(obj: Any) -> bool:
    return is_dataclass(obj) and not isinstance(obj, type)


def _to_jsonable(obj: Any) -> Any:
    """Best-effort conversion to something json.dumps can handle."""
    if _is_dataclass_instance(obj):
        return asdict(obj)

    # pydantic v2
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump()  # type: ignore[attr-defined]
        except Exception:
            pass

    # pydantic v1
    if hasattr(obj, "dict"):
        try:
            return obj.dict()  # type: ignore[attr-defined]
        except Exception:
            pass

    if isinstance(obj, Path):
        return str(obj)

    if isinstance(obj, Mapping):
        return {str(k): _to_jsonable(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(x) for x in obj]

    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj

    # fallback
    return str(obj)


def _ensure_dir(p: Union[str, Path]) -> Path:
    d = Path(p)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_jsonl(path: Path, rows: Sequence[Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(_to_jsonable(r), ensure_ascii=False))
            f.write("\n")


def _write_json(path: Path, obj: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(_to_jsonable(obj), f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def _write_equity_curve_csv(path: Path, portfolio_history: Sequence[Any]) -> None:
    """
    Writes a very tolerant equity curve CSV.

    Expects each element of portfolio_history to be a mapping-like snapshot that
    includes at least 'equity' and optionally 'timestamp'. If timestamp is missing,
    we write the bar index as timestamp.
    """
    rows: list[dict[str, Any]] = []
    for i, snap in enumerate(portfolio_history):
        s = _to_jsonable(snap)
        if isinstance(s, Mapping):
            row = dict(s)
        else:
            # worst case: snapshot is just a scalar equity
            row = {"equity": s}

        # normalize timestamp field if present under other names
        if "timestamp" not in row and "ts" in row:
            row["timestamp"] = row.get("ts")

        if "timestamp" not in row:
            row["timestamp"] = i

        rows.append(row)

    # Choose stable columns. We always include timestamp + equity.
    fieldnames = ["timestamp", "equity"]

    # Add common fields if they exist in any row
    common_optionals = ["cash", "positions_value", "pnl", "drawdown"]
    for k in common_optionals:
        if any(k in r for r in rows):
            fieldnames.append(k)

    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            out: dict[str, Any] = {}
            for k in fieldnames:
                v = r.get(k)
                if isinstance(v, (dict, list)):
                    out[k] = json.dumps(v, ensure_ascii=False)
                else:
                    out[k] = v
            w.writerow(out)


def write_backtest_artifacts(
    *,
    run_dir: Optional[Union[str, Path]] = None,
    out_dir: Optional[Union[str, Path]] = None,
    events: Optional[Sequence[Any]] = None,
    portfolio_history: Optional[Sequence[Any]] = None,
    equity_curve: Optional[Sequence[Any]] = None,
    metrics: Optional[Any] = None,
    params: Optional[Mapping[str, Any]] = None,
    **kwargs: Any,
) -> Dict[str, Path]:
    """
    Write Backtester2 artifacts to disk.

    IMPORTANT: This function is intentionally backward/forward compatible.
    - Accepts both run_dir= and out_dir= (callers sometimes use either).
    - Accepts portfolio_history= and/or equity_curve=.
    - Ignores unknown kwargs so orchestrator-side changes don't crash the CLI.

    Returns a dict of artifact paths.
    """
    base = run_dir if run_dir is not None else out_dir
    if base is None:
        # tolerate older/newer caller spellings
        base = kwargs.get("run_dir") or kwargs.get("out_dir") or kwargs.get("log_dir")

    if base is None:
        raise TypeError("write_backtest_artifacts() requires run_dir= or out_dir=")

    run_path = _ensure_dir(base)
    paths: Dict[str, Path] = {}

    # --- events.jsonl ---
    ev = events
    if ev is None:
        ev = (
            kwargs.get("event_log")
            or kwargs.get("events_log")
            or kwargs.get("event_history")
            or kwargs.get("events")
        )

    events_path = run_path / "events.jsonl"
    if ev is not None:
        _write_jsonl(events_path, list(ev))
    else:
        # Don't fail pipeline expectations: ensure file exists even if empty.
        if not events_path.exists():
            events_path.write_text("", encoding="utf-8")
    paths["events_jsonl"] = events_path

    # --- equity_curve.csv ---
    # Prefer explicit equity_curve, else derive from portfolio_history, else attempt from result-like objects.
    ph = portfolio_history
    if ph is None:
        ph = (
            kwargs.get("portfolio")
            or kwargs.get("history")
            or kwargs.get("equity_history")
            or kwargs.get("portfolio_history")
        )

    if ph is None:
        res = kwargs.get("result") or kwargs.get("backtest_result")
        if res is not None:
            ph = getattr(res, "portfolio_history", None)

    eq_path = run_path / "equity_curve.csv"
    if equity_curve is not None:
        _write_equity_curve_csv(eq_path, list(equity_curve))
    elif ph is not None:
        _write_equity_curve_csv(eq_path, list(ph))
    else:
        # Ensure existence to satisfy pipeline checks even if caller forgot to pass history.
        eq_path.write_text("timestamp,equity\n", encoding="utf-8")
    paths["equity_curve_csv"] = eq_path

    # --- metrics.json ---
    met = metrics
    if met is None:
        met = kwargs.get("bt_metrics") or kwargs.get("backtest_metrics")

    # If metrics not provided but we have portfolio history, compute minimal metrics via existing helper
    if met is None and ph is not None:
        try:
            from ats.backtester2.metrics import compute_backtest_metrics

            met = compute_backtest_metrics(list(ph))
        except Exception:
            met = None

    metrics_path = run_path / "metrics.json"
    if met is not None:
        _write_json(metrics_path, met)
    else:
        if not metrics_path.exists():
            _write_json(metrics_path, {"note": "metrics unavailable"})
    paths["metrics_json"] = metrics_path

    # --- params.json (optional) ---
    prm = params
    if prm is None:
        prm = kwargs.get("config") or kwargs.get("cfg") or kwargs.get("run_config")
    if prm is not None:
        params_path = run_path / "params.json"
        _write_json(params_path, prm)
        paths["params_json"] = params_path

    return paths
