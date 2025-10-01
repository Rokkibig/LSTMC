import numpy as np
import pandas as pd


def ema(s: pd.Series, n: int):
    return s.ewm(span=n, adjust=False).mean()


def rsi(close: pd.Series, n: int = 14):
    delta = close.diff()
    up = delta.clip(lower=0).rolling(n).mean()
    down = -delta.clip(upper=0).rolling(n).mean()
    rs = up / (down + 1e-9)
    return 100 - (100 / (1 + rs))


def atr(df: pd.DataFrame, n: int = 14):
    high, low, close = df["High"], df["Low"], df["Close"]
    true_range = pd.DataFrame(
        {
            "hl": (high - low).abs(),
            "hc": (high - close.shift(1)).abs(),
            "lc": (low - close.shift(1)).abs(),
        }
    ).max(axis=1)
    return ema(true_range, n)


def make_features(df: pd.DataFrame):
    out = df.copy()
    out["RET1"] = out["Close"].pct_change()
    out["EMA20"] = ema(out["Close"], 20)
    out["EMA50"] = ema(out["Close"], 50)
    out["RSI14"] = rsi(out["Close"], 14)
    out["ATR14"] = atr(out, 14)
    
    # Bollinger Bands
    out["BB_mid"] = out["Close"].rolling(20).mean()
    out["BB_std"] = out["Close"].rolling(20).std()
    out["BB_up"] = out["BB_mid"] + 2 * out["BB_std"]
    out["BB_dn"] = out["BB_mid"] - 2 * out["BB_std"]
    out["BB_width"] = (out["BB_up"] - out["BB_dn"]) / out["BB_mid"]
    out["BB_pct"] = (out["Close"] - out["BB_dn"]) / (out["BB_up"] - out["BB_dn"])

    # MACD
    ema12 = ema(out["Close"], 12)
    ema26 = ema(out["Close"], 26)
    out["MACD"] = ema12 - ema26
    out["MACD_signal"] = ema(out["MACD"], 9)
    out["MACD_hist"] = out["MACD"] - out["MACD_signal"]

    out["TrendUp"] = (out["EMA20"] > out["EMA50"]).astype(int)
    return out.dropna().reset_index(drop=True)


def make_targets(df: pd.DataFrame, horizon: int, atr_mult: float):
    f = df.copy()
    f["ATR14"] = f["ATR14"].ffill()
    close = f["Close"].values
    future_max = pd.Series(close).shift(-1).rolling(horizon).max().shift(-(horizon - 1))
    future_min = pd.Series(close).shift(-1).rolling(horizon).min().shift(-(horizon - 1))
    up_th = f["Close"] + atr_mult * f["ATR14"]
    dn_th = f["Close"] - atr_mult * f["ATR14"]
    y = np.zeros(len(f), dtype=int)
    mask_up = (future_max >= up_th) & future_max.notna()
    mask_down = (future_min <= dn_th) & future_min.notna()
    y[mask_up] = 1
    y[mask_down] = -1
    f["y"] = y
    return f.dropna().reset_index(drop=True)

def build_trade(side: str, price: float, atr_value: float, params: dict, rounder: int, confidence: float):
    sl_mult = params["sl_mult"]
    tp1_mult = params["tp1_mult"]
    tp2_mult = params["tp2_mult"]
    if side == "LONG":
        entry = price
        sl = entry - sl_mult * atr_value
        tp1 = entry + tp1_mult * atr_value
        tp2 = entry + tp2_mult * atr_value
    else:
        entry = price
        sl = entry + sl_mult * atr_value
        tp1 = entry - tp1_mult * atr_value
        tp2 = entry - tp2_mult * atr_value
    return {
        "side": side,
        "entry": round(entry, rounder),
        "sl": round(sl, rounder),
        "tp1": round(tp1, rounder),
        "tp2": round(tp2, rounder),
        "confidence": confidence,
    }