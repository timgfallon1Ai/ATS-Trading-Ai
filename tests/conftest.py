from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Optional

import pytest


@dataclass(frozen=True)
class CmdResult:
    cmd: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def output(self) -> str:
        if self.stderr:
            return (self.stdout or "") + "\n" + (self.stderr or "")
        return self.stdout or ""


def _project_root() -> Path:
    # tests/ lives at repo root
    return Path(__file__).resolve().parents[1]


def _base_env(project_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    # Make sure 'ats' is importable even if package install isn't perfect locally.
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(project_root) + (os.pathsep + existing if existing else "")
    env.setdefault("PYTHONUTF8", "1")
    return env


def run_python_module(
    module: str,
    args: list[str],
    *,
    cwd: Optional[Path] = None,
    env: Optional[Mapping[str, str]] = None,
    timeout_s: int = 180,
) -> CmdResult:
    project_root = _project_root()
    run_cwd = cwd or project_root

    merged_env = _base_env(project_root)
    if env:
        merged_env.update({k: str(v) for k, v in env.items()})

    cmd = [sys.executable, "-m", module, *args]
    proc = subprocess.run(
        cmd,
        cwd=str(run_cwd),
        env=merged_env,
        capture_output=True,
        text=True,
        timeout=timeout_s,
    )
    return CmdResult(
        cmd=cmd, returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr
    )


@pytest.fixture()
def project_root() -> Path:
    return _project_root()


@pytest.fixture()
def run_module() -> Callable[[str, list[str]], CmdResult]:
    def _run(module: str, args: list[str], **kwargs) -> CmdResult:
        return run_python_module(module, args, **kwargs)

    return _run
