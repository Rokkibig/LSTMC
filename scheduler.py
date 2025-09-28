
import subprocess
import sys
import yaml
from datetime import datetime

def run_cmd(args: list[str]):
    """Runs a command and streams its output, raising an error if it fails."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] RUN: {' '.join(args)}")
    try:
        # By removing stdout/stderr PIPE, the subprocess output will stream directly.
        # check=True will automatically raise an exception if the command fails.
        subprocess.run(
            args,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR: {' '.join(args)}")
        # The output is already streamed, so we just need to raise the exception
        raise RuntimeError(f"Command failed with exit code {e.returncode}: {' '.join(args)}") from e

def load_cfg() -> dict:
    """Loads the main configuration file."""
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    """Main function to run the entire pipeline."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting pipeline run...")
    
    cfg = load_cfg()

    # Define the sequence of commands
    commands = [
        [
            sys.executable,
            "scripts/fetch_mt5.py",
            "--config",
            "config.yaml",
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
        [sys.executable, "infer_meta_signals.py"], # Run meta-signal inference at the end
    ]

    try:
        for cmd in commands:
            run_cmd(cmd) # Output is now streamed directly, no need to print a return value
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Pipeline run finished successfully.")
    except RuntimeError as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Pipeline failed: {e}")
        # Optionally, add notification logic here (e.g., send an email)
        sys.exit(1)

if __name__ == "__main__":
    main()
