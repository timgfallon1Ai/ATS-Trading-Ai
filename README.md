# ATS-Trading-Ai (scaffold)

Minimal Python scaffold created by an AI assistant. This repo currently contains a tiny package under `src/ats_trading_ai/`, a test, basic formatting/lint config, and a GitHub Actions CI workflow.

Quick start (macOS / zsh)

1) Create and activate a venv

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2) Install the package (editable) and dev dependencies

```bash
python -m pip install --upgrade pip
pip install -e .
pip install -r requirements-dev.txt
```

3) Run tests and linters

```bash
pytest -q
ruff check .
black --check .
```

What I added
- `src/ats_trading_ai/` — tiny package with a sample function (`add`) used by tests.
- `tests/test_core.py` — pytest test for the sample function.
- `requirements-dev.txt` — developer dependencies: pytest, black, ruff.
- `pyproject.toml` — minimal config for Black and Ruff.
- `.github/workflows/ci.yml` — CI that installs dev deps and runs linters + tests on pushes/PRs.
- `.gitignore` — ignores typical Python artifacts and venv.

If you'd like different dependencies, stricter lint rules, or a different project layout, tell me and I will update the scaffold.

Run service CLIs (after `pip install -e .`):

```bash
# run scout
scout

# run trader
trader

Pre-commit (recommended)
-------------------------

Install pre-commit in your development environment and enable the hooks so Black and Ruff run automatically on every commit:

```bash
pip install pre-commit
pre-commit install
```

To validate the hooks against the whole repo (this will auto-fix or format files):

```bash
pre-commit run --all-files
```

Environment setup
-----------------

Create a local `.env` from the example and fill in any credentials you have for integrations:

```bash
cp .env.example .env
# edit .env and add keys like POLYGON_API_KEY, BENZINGA_API_KEY, TWITTER_BEARER_TOKEN, etc.
```


```
