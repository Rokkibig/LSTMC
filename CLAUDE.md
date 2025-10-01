# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Environment Setup
- `python -m venv .venv` - Create virtual environment
- `.venv\Scripts\activate` - Activate virtual environment (Windows)
- `pip install -r requirements.txt` - Install dependencies

### Pipeline Execution
- `python run_pipeline.py` - Run the complete pipeline including meta-learning (preferred method)
- `python run_pipeline.py --timeframes H1,M15` - Run pipeline for specific timeframes only
- `python run_pipeline.py --skip-history` - Skip historical generation (faster for testing)
- `codex run pipeline` - Run basic pipeline via scheduler (without meta-learning)
- `codex run web` - Start the FastAPI web dashboard on http://127.0.0.1:8000
- `python scheduler.py` - Run basic pipeline manually (equivalent to `codex run pipeline`)

### Individual Pipeline Steps
- `python scripts/fetch_mt5.py --config config.yaml --years 20` - Fetch MT5 data
- `python scripts/make_dataset.py --config config.yaml` - Create training datasets
- `python scripts/train_lstm.py --config config.yaml` - Train LSTM models
- `python scripts/infer_signals.py --config config.yaml` - Generate trading signals
- `python infer_meta_signals.py --config config.yaml` - Generate meta-signals using ensemble models

### Meta-Learning Pipeline (included in run_pipeline.py)
- `python historical_generator.py --config config.yaml --days 365` - Generate historical signals for backtesting
- `python label_generator.py --history-dir outputs/history` - Create labeled dataset from historical signals
- `python train_meta_model.py --dataset meta_dataset.csv` - Train LightGBM meta-models
- `python infer_meta_signals.py --config config.yaml` - Generate currency strength predictions and recommended pairs

### Testing
- `pip install pytest` then `pytest` - Run tests (if test files exist in tests/ directory)
- `codex run infer` - Smoke test to verify pipeline generates `outputs/signals.json`

## Architecture Overview

### Core Components
1. **Pipeline Orchestrators**:
   - `run_pipeline.py` - Complete pipeline orchestrator with meta-learning support (recommended)
   - `scheduler.py` - Basic pipeline orchestrator for scheduled runs
2. **scripts/** - Individual pipeline modules:
   - `fetch_mt5.py` - Downloads price data from MetaTrader 5
   - `make_dataset.py` - Prepares training datasets from raw data
   - `train_lstm.py` - Trains TensorFlow LSTM models
   - `infer_signals.py` - Generates trading signals and exports to JSON
   - `web_server.py` - FastAPI server for real-time dashboard
   - `utils.py` - Shared utility functions
3. **Meta-Learning System**:
   - `historical_generator.py` - Creates historical signal snapshots for backtesting
   - `label_generator.py` - Generates labeled datasets from historical signals
   - `train_meta_model.py` - Trains LightGBM meta-models for currency strength prediction
   - `infer_meta_signals.py` - Generates ensemble predictions and recommended currency pairs

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
            train_lstm.py → models/ (LSTM models)
                ↓
            infer_signals.py → outputs/signals.json
                ↓
            historical_generator.py → outputs/history/ (historical signals)
                ↓
            label_generator.py → meta_dataset.csv
                ↓
            train_meta_model.py → models/meta_model_*.joblib
                ↓
            infer_meta_signals.py → outputs/meta_signal.json
                ↓
            web_server.py → Dashboard (reads both JSON files)
```

### Runtime Artifacts
- `data/` - Raw price data from MT5 and prepared metadata files
- `models/` - Trained TensorFlow LSTM models (.h5) and LightGBM meta-models (.joblib)
- `outputs/` - Generated signals (`signals.json`) and meta-signals (`meta_signal.json`)
- `outputs/history/` - Historical signal snapshots organized by date (YYYY-MM-DD/signals.json)
- `meta_dataset.csv` - Labeled dataset generated from historical signals for meta-model training
- These directories and files are git-ignored and created during pipeline execution

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
- Pipeline steps are designed to run sequentially (run_pipeline.py or scheduler.py handle this)
- Each script can be run independently with proper config file
- Meta-learning requires historical data generation (365 days by default) which can take significant time

### Web Dashboard
- FastAPI server only displays data, does not perform computations
- Reads latest signals from `outputs/signals.json` and meta-signals from `outputs/meta_signal.json`
- Provides real-time price feeds and API endpoints at `/api/signals` and `/api/prices`
- Dashboard displays both individual symbol predictions and ensemble currency strength recommendations