
import argparse
import json
import os
import pandas as pd
from tqdm import tqdm
from datetime import timedelta

def flatten_signals(signals: list) -> dict:
    """
    Flattens the list of signal objects into a single dictionary (one row).
    Each feature is prefixed with its symbol and timeframe.
    Example: {'EURUSD_D1_p_short': 0.1, 'EURUSD_D1_trend_up': 1, ...}
    """
    flat_row = {}
    for signal_item in signals:
        symbol = signal_item['symbol']
        tf = signal_item['tf']
        prefix = f"{symbol}_{tf}"
        
        signal_data = signal_item['signal']
        flat_row[f"{prefix}_p_short"] = signal_data['probabilities']['short']
        flat_row[f"{prefix}_p_no"] = signal_data['probabilities']['no']
        flat_row[f"{prefix}_p_long"] = signal_data['probabilities']['long']
        flat_row[f"{prefix}_trend_up"] = 1 if signal_data['trend_up'] else 0
        
    return flat_row

def calculate_currency_strength_labels(current_date: pd.Timestamp, price_data: dict, all_symbols: list, lookahead_hours: int = 24) -> dict:
    """
    Calculates the future return for each major currency to use as a label.
    This is a simplified approach using the currency's pair with USD as a proxy.
    """
    labels = {}
    future_date = current_date + timedelta(hours=lookahead_hours)
    
    unique_currencies = set()
    for s in all_symbols:
        unique_currencies.add(s[:3])
        unique_currencies.add(s[3:])

    for currency in unique_currencies:
        if currency == 'USD':
            continue

        pair = f"{currency}USD"
        inverse = False
        if pair not in all_symbols:
            pair = f"USD{currency}"
            if pair not in all_symbols:
                continue
            inverse = True

        df = price_data.get(pair)
        if df is None:
            continue

        try:
            current_price_rows = df[df['time'] <= current_date]
            if current_price_rows.empty:
                raise IndexError("No data on or before current_date")
            current_price = current_price_rows.iloc[-1]['Close']

            future_price_rows = df[df['time'] >= future_date]
            if future_price_rows.empty:
                raise IndexError("No data on or after future_date")
            future_price = future_price_rows.iloc[0]['Close']
            
            if current_price > 0:
                return_pct = (future_price - current_price) / current_price
                if inverse:
                    return_pct = -return_pct
                labels[f"{currency}_target"] = return_pct
            else:
                labels[f"{currency}_target"] = 0

        except IndexError:
            labels[f"{currency}_target"] = None # Use None for missing data
            
    return labels

def main():
    parser = argparse.ArgumentParser(description="Generate labels for historical signal data.")
    parser.add_argument("--history-dir", default="outputs/history", help="Directory with historical signal files.")
    parser.add_argument("--data-dir", default="data", help="Directory with historical price CSVs.")
    parser.add_argument("--outfile", default="meta_dataset.csv", help="Output CSV file for the dataset.")
    args = parser.parse_args()

    print("Pre-loading all D1 price data...")
    price_data = {}
    all_symbols = []
    for filename in os.listdir(args.data_dir):
        if filename.endswith("_D1.csv"):
            symbol = filename.replace("_D1.csv", '')
            all_symbols.append(symbol)
            df = pd.read_csv(os.path.join(args.data_dir, filename), parse_dates=['time'])
            price_data[symbol] = df
    
    all_rows = []
    history_dates = sorted([d for d in os.listdir(args.history_dir) if os.path.isdir(os.path.join(args.history_dir, d))])
    
    print(f"Generating features and labels for {len(history_dates)} days...")
    for date_str in tqdm(history_dates, desc="Processing historical data"):
        signal_file_path = os.path.join(args.history_dir, date_str, "signals.json")
        
        if not os.path.exists(signal_file_path):
            continue
            
        with open(signal_file_path, 'r', encoding='utf-8') as f:
            try:
                daily_signals = json.load(f)
            except json.JSONDecodeError:
                continue

        if not daily_signals.get('signals'):
            continue

        features = flatten_signals(daily_signals['signals'])
        if not features:
            continue
        
        current_date = pd.to_datetime(date_str)
        labels = calculate_currency_strength_labels(current_date, price_data, all_symbols)
        
        combined_row = {'date': date_str, **features, **labels}
        all_rows.append(combined_row)

    if not all_rows:
        print("No data was processed. Exiting.")
        return

    final_df = pd.DataFrame(all_rows)
    final_df['date'] = pd.to_datetime(final_df['date'])
    final_df = final_df.set_index('date').sort_index()
    
    # Drop rows where all labels are missing, which happens at the end of the dataset
    label_cols = [col for col in final_df.columns if '_target' in col]
    final_df.dropna(subset=label_cols, how='all', inplace=True)

    final_df.to_csv(args.outfile)
    print(f"\n[DONE] Meta dataset created successfully at {args.outfile}")
    print(f"Dataset has {len(final_df)} rows and {len(final_df.columns)} columns.")

if __name__ == "__main__":
    main()
