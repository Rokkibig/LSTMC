from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os
import json
from datetime import datetime

app = FastAPI(title="LSTM Forex Signals API")

SIGNALS_FILE = "/home/aiagent1/LSTMC/outputs/signals.json"

@app.get("/")
def index():
    return {
        "service": "LSTM Forex Signals API",
        "status": "running",
        "version": "1.0"
    }

@app.get("/api/signals")
def get_signals():
    if os.path.exists(SIGNALS_FILE):
        with open(SIGNALS_FILE) as f:
            data = json.load(f)
        return data
    return {"error": "No signals available yet"}

@app.get("/api/health")
def health():
    signals_exist = os.path.exists(SIGNALS_FILE)
    if signals_exist:
        mtime = os.path.getmtime(SIGNALS_FILE)
        updated = datetime.fromtimestamp(mtime).isoformat()
    else:
        updated = None

    return {
        "status": "ok",
        "signals_available": signals_exist,
        "last_update": updated
    }
