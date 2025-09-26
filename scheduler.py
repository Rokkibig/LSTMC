
import subprocess
import sys
import yaml
from datetime import datetime

def run_cmd(args: list[str]) -> str:
    """Runs a command and returns its output, raising an error if it fails."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] RUN: {' '.join(args)}")
    proc = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR: {' '.join(args)}")
        print(proc.stdout)
        raise RuntimeError(f"Command failed with exit code {proc.returncode}: {' '.join(args)}")
    return proc.stdout

def load_cfg() -> dict:
    """Loads the main configuration file."""
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    """Main function to run the entire pipeline."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting pipeline run...")
    
    cfg = load_cfg()
    max_years = int(cfg.get("years_max", 15))

    # Define the sequence of commands
    commands = [
        [
            sys.executable,
            "scripts/fetch_mt5.py",
            "--config",
            "config.yaml",
            "--years",
            str(max_years),
        ],
        [sys.executable, "scripts/make_dataset.py", "--config", "config.yaml"],
        [sys.executable, "scripts/train_lstm.py", "--config", "config.yaml"],
        [
            sys.executable,
            "scripts/infer_signals.py",
            "--config",
            "config.yaml",
            "--out",
            "outputs/signals.json",
        ],
    ]

    try:
        for cmd in commands:
            log_output = run_cmd(cmd)
            print(log_output)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Pipeline run finished successfully.")
    except RuntimeError as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Pipeline failed: {e}")
        # Optionally, add notification logic here (e.g., send an email)
        sys.exit(1)

if __name__ == "__main__":
    main()
