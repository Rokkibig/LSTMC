import argparse, os
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import yaml

def load_cfg(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def fetch(symbol: str, tf, tf_name: str, years: int, outdir: str):
    to = datetime.now()
    frm = to - timedelta(days=365*years + 30)
    rates = mt5.copy_rates_range(symbol, tf, frm, to)
    if rates is None or len(rates) == 0:
        print(f"[WARN] No data for {symbol} {tf_name}")
        return 0
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df = df.rename(columns={"open":"Open","high":"High","low":"Low","close":"Close","tick_volume":"Volume"})
    df = df[["time","Open","High","Low","Close","Volume"]]
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f"{symbol}_{tf_name}.csv")
    df.to_csv(path, index=False)
    print(f"[OK] Saved {path} rows={len(df)}")
    return len(df)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--years", type=int, default=None, help="override years (<= years_max)")
    ap.add_argument("--outdir", default="data")
    args = ap.parse_args()

    cfg = load_cfg(args.config)
    years_max = cfg.get("years_max", 15)
    years = args.years if args.years else years_max
    years = min(years, years_max)

    if not mt5.initialize():
        raise SystemExit("MT5 init failed")
    TF_MAP = {
        "D1": mt5.TIMEFRAME_D1,
        "H4": mt5.TIMEFRAME_H4,
        "H2": mt5.TIMEFRAME_H2,
        "M30": mt5.TIMEFRAME_M30,
        "M15": mt5.TIMEFRAME_M15,
    }
    total = 0
    for s in cfg["symbols"]:
        for tf_name in cfg["timeframes"].keys():
            total += fetch(s, TF_MAP[tf_name], tf_name, years, args.outdir)
    mt5.shutdown()
    print(f"[DONE] Total rows saved: {total}")

if __name__ == "__main__":
    main()
