## Copilot / AI agent instructions for ATS-Trading-Ai

Repository snapshot (discoverable):
- Current branch: `main` (local workspace)
- Files present at repo root: `.gitattributes` and `.git/` only — there are no source files, README, or CI config in this clone.

If you (an AI coding agent) open this repo, follow these prioritized steps:

1. Confirm repository state
   - Run `git fetch --all --prune` and `git branch -avv` to see remote branches and refs.
   - Check `git remote -v` to confirm where authoritative source code may live.

2. If the repository is intentionally empty here
   - Ask the human owner whether they want you to: (A) pull from a remote branch, (B) scaffold the project, or (C) work against a different folder.
   - If a remote contains code, prefer to inspect the remote branch before creating files locally.

3. When code is present (how to behave)
   - Look for Python project conventions first (common names: `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile`) and a `src/` or `app/` directory.
   - Identify entry points: scripts under `bin/`, `main.py`, or `src/` packages. Note any `Dockerfile` or `.github/workflows` for CI hints.

4. Project-specific guidance (based on current discoverable state)
   - There are no discoverable source files in this clone. Do not assume frameworks, languages, or test runners.
   - Avoid making large scaffolding changes without confirmation. Provide a minimal proposal first (README + basic layout) and wait for approval.

5. Merging guidance (if a previous `.github/copilot-instructions.md` exists remotely)
   - Preserve any human-written guidance. Merge only to add up-to-date discovery results (files present, branches, remote URL) and clear next actions.

6. Example prompts/actions you can propose to the repo owner
   - "I see no source files locally. Should I fetch remote branches to look for the project, or would you like me to scaffold a starter layout (Python/Node)?"
   - If asked to scaffold, propose a minimal structure: `README.md`, `src/` or `app/`, `tests/`, `requirements.txt` / `pyproject.toml`, and CI workflow under `.github/workflows/ci.yml`.

   ---

   When this repository is scaffolded into a multi-service ATS
   -----------------------------------------------

   If the repo contains the multi-service layout (see files below), follow these rules:

   - Architecture overview (discoverable files):
      - `src/ats_trading_ai/` — original package used by unit tests (keep this working).
      - `ats/` — core logic: `feature_extraction.py`, `backtesting.py`, `cache.py`.
      - `services/` — microservice stubs in `services/{scout,deep_backtester,trader,analyst}`.
      - `libs/` — shared utils, e.g. `libs/utils.py`.
      - `schemas/` — JSON Schema contracts (e.g. `schemas/trade.schema.json`).
      - `docker-compose.yml` and `.env.example` — quick local dev orchestration.

   - Developer workflow (how to run things locally):
      1. Create a venv and activate it (macOS / zsh):

          ```bash
          python3 -m venv .venv
          source .venv/bin/activate
          ```

      2. Install editable package and dev deps:

          ```bash
          python -m pip install --upgrade pip
          pip install -e .
          pip install -r requirements-dev.txt
          ```

      3. Run tests and linters:

          ```bash
          pytest -q
          ruff check .
          black --check .
          ```

   - Conventions and patterns to preserve:
      - Keep `src/` as the canonical installable package root (setuptools find configured in `pyproject.toml`).
      - New services under `services/` are lightweight stubs by default; they may later be moved to their own packages or Dockerfiles.
      - Shared logic belongs in `ats/` (pure algorithms) or `libs/` (helpers). Prefer small, pure functions for core logic so unit tests remain fast.
      - JSON schemas in `schemas/` are the contract for service inputs/outputs; reference them in service code and validate inputs in tests where possible.

   - CI notes:
      - CI installs the package editable (`pip install -e .`) before running linters and tests.
      - Keep CI steps fast: unit tests should not require external services by default. If a service needs external resources, mock them in tests and add an `integration` job separately.

   Reference files you can read to learn the layout quickly:
   - `pyproject.toml`, `requirements-dev.txt`, `tests/test_core.py`, `src/ats_trading_ai/core.py`, `ats/feature_extraction.py`, `services/scout/scout.py`, `schemas/trade.schema.json`, `docker-compose.yml`.

   If anything here is stale or you want a different organization (for example, moving each service into its own independent package and Dockerfile), ask and I will propose a migration plan.

7. Quick checklist for PRs produced by the agent
   - Keep changes minimal and linear: one feature or scaffold per PR.
   - Add a one-line summary in the PR describing why files were created and how to run locally.

Contact / follow-up
- If anything here is unclear, ask the repo owner for the canonical remote URL and their preferred language/runtime. If you need me to create an initial scaffold now, reply with the desired stack (Python/Node/Go) and I will implement a minimal layout.

-- end of instructions --
