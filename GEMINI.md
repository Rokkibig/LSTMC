## Project Overview

This project is an automated pipeline for generating Forex trading signals. It uses MetaTrader 5 for data, a Long Short-Term Memory (LSTM) neural network built with TensorFlow/Keras for prediction, and a FastAPI web server for monitoring.

The system is designed for automated, scheduled execution. A central script (`scheduler.py`) runs the entire pipeline, from data fetching to signal generation. A separate web server (`scripts/web_server.py`) provides a real-time dashboard to view the latest generated signals and live Forex prices.

### Key Technologies

*   **Data Source:** MetaTrader 5
*   **Machine Learning:** TensorFlow/Keras (LSTM)
*   **Web Framework:** FastAPI
*   **Orchestration:** Python script (`scheduler.py`) intended for use with a system scheduler (e.g., Windows Task Scheduler, cron).

## Building and Running

### Prerequisites

*   Python 3.10+
*   A running MetaTrader 5 terminal, logged into an account.

### Key Commands

The project uses shortcuts defined in `codex.yaml`:

*   **Run the full pipeline (manual execution):**
    ```bash
    codex run pipeline
    ```
    This command executes `scheduler.py`, which runs all the steps: fetching data, creating datasets, training models, and inferring signals. This is useful for testing or manual runs.

*   **Start the web dashboard:**
    ```bash
    codex run web
    ```
    This starts the FastAPI server. You can access the dashboard at `http://127.0.0.1:8000`.

For automated execution, `scheduler.py` should be configured to run as a scheduled task. See `DEPLOY.md` for detailed instructions.

## Development Conventions

*   **Configuration:** All main parameters (symbols, timeframes, model hyperparameters) are managed in `config.yaml`.
*   **Modularity:** The project is split into distinct scripts for each stage of the pipeline (`fetch_mt5.py`, `make_dataset.py`, `train_lstm.py`, `infer_signals.py`), which are orchestrated by `scheduler.py`.
*   **API:** The web server exposes a clean, read-only API for accessing results.
    *   `GET /api/signals`: Provides the latest trading signals.
    *   `GET /api/prices`: Provides real-time prices.
*   **Deployment:** The `DEPLOY.md` file contains detailed instructions for setting up the project on a Windows Server for automated operation.
