"""
Training Scheduler для Linux Server
Забирає дані з Windows MT5 API і тренує моделі
"""

import os
import sys
import time
import requests
import yaml
import subprocess
from datetime import datetime, time as dtime
from pathlib import Path

# Environment
WINDOWS_API = os.getenv("WINDOWS_MT5_API", "http://84.247.166.52:5000")
LOG_FILE = "logs/training.log"


def log(message):
    """Write to log file and stdout"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    print(log_message)

    Path("logs").mkdir(exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_message + "\n")


def check_windows_api():
    """Check if Windows MT5 API is accessible"""
    try:
        response = requests.get(f"{WINDOWS_API}/api/mt5/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            log(f"✅ Windows MT5 API: {data.get('status')}")
            return True
        else:
            log(f"❌ Windows API returned {response.status_code}")
            return False
    except Exception as e:
        log(f"❌ Cannot reach Windows API: {e}")
        return False


def fetch_data_from_windows():
    """Fetch historical data from Windows server"""
    log("📥 Fetching data from Windows MT5 API...")

    # Load config
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    symbols = config.get("symbols", [])
    timeframes = config.get("timeframes", {})

    total_downloaded = 0

    for symbol in symbols:
        for tf, tf_config in timeframes.items():
            years = tf_config.get("years", 5)

            try:
                url = f"{WINDOWS_API}/api/mt5/history/{symbol}/{tf}?years={years}"
                response = requests.get(url, timeout=120)

                if response.status_code == 200:
                    data = response.json()
                    bars_count = data.get("bars_count", 0)
                    total_downloaded += bars_count
                    log(f"  ✅ {symbol} {tf}: {bars_count} bars")

                    # Save to local cache
                    Path(f"data/{symbol}").mkdir(parents=True, exist_ok=True)
                    filename = f"data/{symbol}/{tf}.json"
                    with open(filename, "w") as f:
                        import json
                        json.dump(data, f)
                else:
                    log(f"  ❌ {symbol} {tf}: HTTP {response.status_code}")
            except Exception as e:
                log(f"  ❌ {symbol} {tf}: {e}")

    log(f"📊 Total downloaded: {total_downloaded} bars")
    return total_downloaded > 0


def run_training(mode="quick"):
    """Run training pipeline"""
    if mode == "quick":
        log("🚀 Starting QUICK training (30 min)...")
        cmd = "python run_improved_pipeline.py --skip-history"
    elif mode == "full":
        log("🚀 Starting FULL training (2-4 hours)...")
        cmd = "python run_improved_pipeline.py --model-type ensemble --meta-ensemble --cv-folds 5"
    elif mode == "m15":
        log("🚀 Starting M15 specialized training (15 min)...")
        cmd = "python scripts/train_lstm.py --config config.yaml --model-type gru"
    else:
        log(f"❌ Unknown training mode: {mode}")
        return False

    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        log(f"✅ Training completed successfully")
        log(f"Output: {result.stdout[-500:]}")  # Last 500 chars
        return True
    except subprocess.CalledProcessError as e:
        log(f"❌ Training failed: {e}")
        log(f"Error: {e.stderr[-500:]}")
        return False


def should_run_quick_retrain():
    """Check if it's time for daily quick retrain (01:00)"""
    now = datetime.now()
    target_time = dtime(1, 0)  # 01:00
    return now.time().hour == target_time.hour and now.time().minute < 5


def should_run_full_retrain():
    """Check if it's time for Saturday full retrain (02:00)"""
    now = datetime.now()
    is_saturday = now.weekday() == 5  # Saturday
    target_time = dtime(2, 0)  # 02:00
    return is_saturday and now.time().hour == target_time.hour and now.time().minute < 5


def should_run_m15_retrain():
    """Check if it's time for M15 evening retrain (23:00)"""
    now = datetime.now()
    target_time = dtime(23, 0)  # 23:00
    return now.time().hour == target_time.hour and now.time().minute < 5


def main():
    """Main scheduler loop"""
    log("=" * 60)
    log("🤖 Forex ML Training Scheduler")
    log("=" * 60)

    # Check Windows API
    if not check_windows_api():
        log("⚠️ WARNING: Windows API not reachable. Will retry...")

    last_quick_run = None
    last_full_run = None
    last_m15_run = None

    log("⏰ Scheduler started. Waiting for scheduled times...")
    log("  - Daily quick: 01:00")
    log("  - Saturday full: 02:00")
    log("  - M15 evening: 23:00")

    while True:
        try:
            now = datetime.now()

            # Quick retrain (01:00 daily)
            if should_run_quick_retrain():
                if last_quick_run != now.date():
                    log("\n🔔 Time for DAILY QUICK RETRAIN")
                    if fetch_data_from_windows():
                        run_training("quick")
                    last_quick_run = now.date()

            # Full retrain (02:00 Saturday)
            elif should_run_full_retrain():
                if last_full_run != now.date():
                    log("\n🔔 Time for SATURDAY FULL RETRAIN")
                    if fetch_data_from_windows():
                        run_training("full")
                    last_full_run = now.date()

            # M15 retrain (23:00 daily)
            elif should_run_m15_retrain():
                if last_m15_run != now.date():
                    log("\n🔔 Time for M15 EVENING RETRAIN")
                    if fetch_data_from_windows():
                        run_training("m15")
                    last_m15_run = now.date()

            # Sleep for 1 minute
            time.sleep(60)

        except KeyboardInterrupt:
            log("\n👋 Scheduler stopped by user")
            break
        except Exception as e:
            log(f"❌ Scheduler error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    main()
