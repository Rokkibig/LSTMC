# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Environment Setup
- `python -m venv .venv` - Create virtual environment
- `.venv\Scripts\activate` - Activate virtual environment (Windows)
- `pip install -r requirements.txt` - Install dependencies

### Pipeline Execution
- `codex run pipeline` - Run the complete data pipeline (fetch → dataset → train → infer)
- `codex run web` - Start the FastAPI web dashboard on http://127.0.0.1:8000
- `python scheduler.py` - Run pipeline manually (equivalent to `codex run pipeline`)

### Individual Pipeline Steps
- `python scripts/fetch_mt5.py --config config.yaml --years 20` - Fetch MT5 data
- `python scripts/make_dataset.py --config config.yaml` - Create training datasets
- `python scripts/train_lstm.py --config config.yaml` - Train LSTM models
- `python scripts/infer_signals.py --config config.yaml` - Generate trading signals

### Testing
- `pip install pytest` then `pytest` - Run tests (if test files exist in tests/ directory)
- `codex run infer` - Smoke test to verify pipeline generates `outputs/signals.json`

## Architecture Overview

### Core Components
1. **scheduler.py** - Main orchestrator that runs the entire pipeline sequentially
2. **scripts/** - Individual pipeline modules:
   - `fetch_mt5.py` - Downloads price data from MetaTrader 5
   - `make_dataset.py` - Prepares training datasets from raw data
   - `train_lstm.py` - Trains TensorFlow LSTM models
   - `infer_signals.py` - Generates trading signals and exports to JSON
   - `web_server.py` - FastAPI server for real-time dashboard
   - `utils.py` - Shared utility functions

### Configuration System
- **config.yaml** - Central configuration for symbols, timeframes, model parameters, and thresholds
- **codex.yaml** - Command shortcuts for pipeline and web server
- All scripts accept `--config config.yaml` parameter for consistency

### Data Flow
```
MT5 Terminal → fetch_mt5.py → data/
                ↓
            make_dataset.py → prepared datasets
                ↓
            train_lstm.py → models/
                ↓
            infer_signals.py → outputs/signals.json
                ↓
            web_server.py → Dashboard (reads signals.json)
```

### Runtime Artifacts
- `data/` - Raw price data from MT5
- `models/` - Trained TensorFlow models
- `outputs/` - Generated signals and results
- These directories are git-ignored and created during pipeline execution

## Development Guidelines

### Code Style
- Follow PEP 8 with 4-space indentation
- Use snake_case for functions/variables, UpperCamelCase for classes
- Import order: standard library, third-party, local modules
- Derive paths from config.yaml rather than hard-coding

### Configuration Management
- Update `config.yaml` for symbols, timeframes, and model parameters instead of modifying code
- Use environment variables for sensitive data (MT5 credentials in `.env`)
- Never commit `.env` files or credential information

### Pipeline Dependencies
- MetaTrader 5 terminal must be running and logged in for data fetching
- Pipeline steps are designed to run sequentially (scheduler.py handles this)
- Each script can be run independently with proper config file

### Web Dashboard
- FastAPI server only displays data, does not perform computations
- Reads latest signals from `outputs/signals.json`
- Provides real-time price feeds and API endpoints at `/api/signals` and `/api/prices`