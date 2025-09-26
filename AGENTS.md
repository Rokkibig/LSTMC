# Repository Guidelines

## Project Structure & Module Organization
- `scripts/` hosts operational modules: `fetch_mt5.py` downloads MT5 price data, `make_dataset.py` builds datasets, `train_lstm.py` trains TensorFlow models, `infer_signals.py` exports JSON signals, and `web_server.py` exposes FastAPI endpoints.
- Configuration lives in `config.yaml` (symbols, timeframes, thresholds). Update values there instead of hard-coding.
- Runtime artifacts land in `data/`, `models/`, and `outputs/` once scripts run; keep them git-ignored and review sizes before sharing.
- `requirements.txt` pins runtime dependencies, while `codex.yaml` wraps the automation shortcuts.

## Build, Test, and Development Commands
- `python -m venv .venv` then `.venv\Scripts\activate` to provision a local virtual environment.
- `pip install -r requirements.txt` installs MT5, TensorFlow, FastAPI, and supporting libraries.
- `codex run fetch | dataset | train | infer | web` executes the full pipeline with the shared `config.yaml`.
- Invoke individual modules with `python scripts/train_lstm.py --config config.yaml` (swap in other scripts while debugging).

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation; group imports as standard library, third-party, then local.
- Use `snake_case` for functions and variables, `UpperCamelCase` for classes, and uppercase constants for configuration keys.
- Add docstrings or comments only when behavior is non-obvious; place reusable helpers in `scripts/utils.py`.
- Avoid hard-coded paths; derive them from `config.yaml` or environment variables so Codex runs stay portable.

## Testing Guidelines
- Smoke-test data flows with `codex run infer` after any processing change; confirm it refreshes `outputs/signals.json`.
- Add automated tests under a `tests/` package and target them with `pytest` (install with `pip install pytest`). Name files `test_<feature>.py` and mirror script namespaces.
- Maintain reproducibility by seeding NumPy and TensorFlow (`np.random.seed`, `tf.random.set_seed`) inside new training routines.

## Commit & Pull Request Guidelines
- Write imperative commit subjects such as Add MT5 retry logic, keep them <= 72 characters, and mention the touched scope when useful (`train`, `infer`, `web`).
- Reference issue IDs in the body when applicable and record the commands or scenarios used for validation.
- Pull requests should outline objectives, summarize key code changes, list verification steps, and include API screenshots or payload samples when FastAPI behavior changes.
- Request review from domain owners before merging; ensure smoke tests or CI jobs have run and are linked.

## Security & Configuration Tips
- Store MT5 credentials in `.env`; never commit `.env` or generated JSON payloads that hold tokens.
- Rotate `API_TOKEN` regularly and update dependent services. Prefer OS-level secret stores for long-term keys.
- Limit FastAPI exposure when running `codex run web`; bind to `127.0.0.1` during local testing unless remote access is required.
