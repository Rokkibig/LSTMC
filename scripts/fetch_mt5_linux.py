"""
Fetch MT5 data from Windows API for Linux server
"""
import argparse, os
import pandas as pd
import yaml
import requests

def load_cfg(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def fetch(symbol: str, tf_name: str, years: int, outdir: str, api_url: str):
    """Fetch data from Windows MT5 API"""
    try:
        # Calculate approximate count from years
        # Rough estimates: D1=365, H4=2190, H1=8760, M30=17520, M15=35040 bars per year
        timeframe_bars_per_year = {
            "D1": 365,
            "H4": 2190,
            "H2": 4380,
            "H1": 8760,
            "M30": 17520,
            "M15": 35040
        }
        count = timeframe_bars_per_year.get(tf_name, 8760) * years

        url = f"{api_url}/api/history"
        params = {
            "symbol": symbol,
            "timeframe": tf_name,
            "count": count
        }
        response = requests.get(url, params=params, timeout=120)

        if response.status_code != 200:
            print(f"[WARN] API error for {symbol} {tf_name}: {response.status_code}")
            return 0

        data = response.json()

        if data.get("status") != "ok":
            print(f"[WARN] API error for {symbol} {tf_name}: {data.get('error', 'Unknown error')}")
            return 0

        # Convert to DataFrame
        df = pd.DataFrame(data["data"])
        df["time"] = pd.to_datetime(df["time"])

        # Rename columns to match expected format
        # API may return different column names, handle both cases
        rename_map = {
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "tick_volume": "Volume",
            "volume": "Volume"
        }
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

        # Select only needed columns
        df = df[["time", "Open", "High", "Low", "Close", "Volume"]]

        # Save to CSV
        os.makedirs(outdir, exist_ok=True)
        path = os.path.join(outdir, f"{symbol}_{tf_name}.csv")
        df.to_csv(path, index=False)

        print(f"[OK] Saved {path} rows={len(df)} (from Windows API)")
        return len(df)

    except Exception as e:
        print(f"[ERROR] Failed to fetch {symbol} {tf_name}: {e}")
        return 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--outdir", default="data")
    ap.add_argument("--api-url", default="http://84.247.166.52:5000",
                    help="Windows MT5 API URL")
    args = ap.parse_args()

    cfg = load_cfg(args.config)

    total = 0
    for s in cfg["symbols"]:
        for tf_name, tf_cfg in cfg["timeframes"].items():
            years = tf_cfg.get("years", 5)
            total += fetch(s, tf_name, years, args.outdir, args.api_url)

    print(f"[DONE] Total rows saved: {total}")

if __name__ == "__main__":
    main()
