import argparse
import glob
import os
import subprocess
import sys
from datetime import datetime

def run_cmd(args: list[str]):
    """Runs a command and streams its output, raising an error if it fails."""
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] RUN: {' '.join(args)}")
    try:
        subprocess.run(args, check=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR: {' '.join(args)}")
        raise RuntimeError(f"Command failed with exit code {e.returncode}: {' '.join(args)}") from e

def main():
    parser = argparse.ArgumentParser(description="Orchestrator for the full Forex ML pipeline.")
    parser.add_argument(
        "--timeframes",
        type=str,
        help="Optional: Comma-separated list of timeframes to process (e.g., H1,M15). If not provided, all timeframes from config will be used.",
    )
    parser.add_argument(
        "--skip-history",
        action="store_true",
        help="Optional: Skip the long historical generation step.",
    )
    args = parser.parse_args()

    # Base commands that always run
    base_pipeline = [
        {"name": "Fetch Data", "cmd": [sys.executable, "-m", "scripts.fetch_mt5", "--config", "config.yaml"]},
        {"name": "Create Datasets", "cmd": [sys.executable, "-m", "scripts.make_dataset", "--config", "config.yaml"]},
        {"name": "Train Base Models", "cmd": [sys.executable, "-m", "scripts.train_lstm", "--config", "config.yaml"]},
    ]

    # Meta-model pipeline
    meta_pipeline = [
        {
            "name": "Generate History",
            "cmd": [sys.executable, "-m", "historical_generator", "--config", "config.yaml"],
            "skip_flag": args.skip_history,
        },
        {"name": "Generate Labels", "cmd": [sys.executable, "-m", "label_generator"]},
        {"name": "Train Meta-Model", "cmd": [sys.executable, "-m", "train_meta_model"]},
    ]

    # Final inference commands
    inference_pipeline = [
        {
            "name": "Infer Base Signals",
            "cmd": [
                sys.executable,
                "-m",
                "scripts.infer_signals",
                "--config",
                "config.yaml",
                "--out",
                "outputs/signals.json",
            ],
        },
        {"name": "Infer Meta Signal", "cmd": [sys.executable, "-m", "infer_meta_signals"]},
    ]

    # If specific timeframes are provided, add them as an argument to the relevant commands
    if args.timeframes:
        for step in base_pipeline:
            if "make_dataset.py" in step["cmd"] or "train_lstm.py" in step["cmd"]:
                step["cmd"].extend(["--timeframes", args.timeframes])
        # Note: History generation and inference steps usually run on all TFs
        # to provide full context for the meta-model. We don't filter them.

    # --- Execute Pipeline ---
    all_steps = base_pipeline + meta_pipeline + inference_pipeline
    total_steps = len([s for s in all_steps if not s.get("skip_flag")])
    current_step = 1

    print("--- Starting Full Pipeline Run ---")
    try:
        # Clean old meta-models before starting
        print("\n[STEP 0] Deleting old meta-models...")
        for f in glob.glob("models/meta_model_*.joblib"):
            os.remove(f)
            print(f"Removed {f}")

        for step in all_steps:
            if step.get("skip_flag"):
                print(f"\n--- SKIPPING STEP: {step['name']} ---")
                continue
            
            print(f"\n--- STEP {current_step}/{total_steps}: {step['name']} ---")
            run_cmd(step["cmd"])
            current_step += 1
        
        print("\n[SUCCESS] Full pipeline completed successfully.")

    except (RuntimeError, FileNotFoundError) as e:
        print(f"\n[FATAL] Pipeline failed at step: {step['name']}.")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
