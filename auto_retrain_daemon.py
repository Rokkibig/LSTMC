"""
Автоматичний daemon для щоденного перенавчання моделей
Запускає pipeline кожні 24 години
"""

import time
import subprocess
import sys
from datetime import datetime
import logging

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/auto_retrain.log'),
        logging.StreamHandler()
    ]
)

def run_retraining():
    """Запускає повний pipeline перенавчання"""
    logging.info("=" * 60)
    logging.info("Starting automatic retraining...")
    logging.info("=" * 60)

    try:
        # Запускаємо pipeline (без історії для швидкості)
        result = subprocess.run(
            [sys.executable, "run_improved_pipeline.py", "--skip-history"],
            check=True,
            capture_output=True,
            text=True
        )

        logging.info("Retraining completed successfully!")
        logging.info(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
        return True

    except subprocess.CalledProcessError as e:
        logging.error(f"Retraining failed with error: {e}")
        logging.error(f"Output: {e.output}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return False

def main():
    """Головний цикл daemon"""
    logging.info("Auto-retrain daemon started")
    logging.info("Will retrain models every 24 hours")

    # Опціонально: запустити одразу при старті
    run_on_startup = input("Run retraining immediately on startup? (y/n): ").lower() == 'y'

    if run_on_startup:
        logging.info("Running initial retraining...")
        run_retraining()

    while True:
        try:
            # Розрахувати час до наступного запуску
            now = datetime.now()
            target_hour = 0  # Запускати о 00:00

            next_run = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
            if next_run <= now:
                # Якщо вже пройшла ця година сьогодні, запланувати на завтра
                from datetime import timedelta
                next_run += timedelta(days=1)

            sleep_seconds = (next_run - now).total_seconds()

            logging.info(f"Next retraining scheduled at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            logging.info(f"Sleeping for {sleep_seconds/3600:.1f} hours...")

            # Спати до наступного запуску
            time.sleep(sleep_seconds)

            # Запустити перенавчання
            run_retraining()

        except KeyboardInterrupt:
            logging.info("Daemon stopped by user")
            break
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            logging.info("Retrying in 1 hour...")
            time.sleep(3600)

if __name__ == "__main__":
    import os
    os.makedirs("logs", exist_ok=True)
    main()
