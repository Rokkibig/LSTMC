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

    # Basic price features
    out["RET1"] = out["Close"].pct_change()
    out["RET5"] = out["Close"].pct_change(periods=5)
    out["RET10"] = out["Close"].pct_change(periods=10)
    out["LogRet"] = np.log(out["Close"] / out["Close"].shift(1))

    # Moving Averages
    out["EMA8"] = ema(out["Close"], 8)
    out["EMA20"] = ema(out["Close"], 20)
    out["EMA50"] = ema(out["Close"], 50)
    out["EMA100"] = ema(out["Close"], 100)
    out["SMA20"] = out["Close"].rolling(20).mean()
    out["SMA50"] = out["Close"].rolling(50).mean()

    # RSI variations
    out["RSI14"] = rsi(out["Close"], 14)
    out["RSI7"] = rsi(out["Close"], 7)
    out["RSI21"] = rsi(out["Close"], 21)

    # ATR variations
    out["ATR14"] = atr(out, 14)
    out["ATR7"] = atr(out, 7)
    out["ATR_pct"] = out["ATR14"] / out["Close"]

    # Bollinger Bands
    out["BB_mid"] = out["Close"].rolling(20).mean()
    out["BB_std"] = out["Close"].rolling(20).std()
    out["BB_up"] = out["BB_mid"] + 2 * out["BB_std"]
    out["BB_dn"] = out["BB_mid"] - 2 * out["BB_std"]
    out["BB_width"] = (out["BB_up"] - out["BB_dn"]) / out["BB_mid"]
    out["BB_pct"] = (out["Close"] - out["BB_dn"]) / (out["BB_up"] - out["BB_dn"] + 1e-9)

    # MACD
    ema12 = ema(out["Close"], 12)
    ema26 = ema(out["Close"], 26)
    out["MACD"] = ema12 - ema26
    out["MACD_signal"] = ema(out["MACD"], 9)
    out["MACD_hist"] = out["MACD"] - out["MACD_signal"]

    # Momentum Indicators
    out["MOM"] = out["Close"] - out["Close"].shift(10)
    out["ROC"] = out["Close"].pct_change(periods=10) * 100

    # Stochastic Oscillator
    low_min = out["Low"].rolling(14).min()
    high_max = out["High"].rolling(14).max()
    out["Stoch_K"] = 100 * (out["Close"] - low_min) / (high_max - low_min + 1e-9)
    out["Stoch_D"] = out["Stoch_K"].rolling(3).mean()

    # CCI (Commodity Channel Index)
    tp = (out["High"] + out["Low"] + out["Close"]) / 3
    out["CCI"] = (tp - tp.rolling(20).mean()) / (0.015 * tp.rolling(20).std() + 1e-9)

    # Williams %R
    out["WilliamsR"] = -100 * (high_max - out["Close"]) / (high_max - low_min + 1e-9)

    # ADX (Average Directional Index)
    plus_dm = out["High"].diff()
    minus_dm = -out["Low"].diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    tr = pd.concat([out["High"] - out["Low"],
                    (out["High"] - out["Close"].shift()).abs(),
                    (out["Low"] - out["Close"].shift()).abs()], axis=1).max(axis=1)
    atr_14 = tr.rolling(14).mean()
    plus_di = 100 * (plus_dm.rolling(14).mean() / atr_14)
    minus_di = 100 * (minus_dm.rolling(14).mean() / atr_14)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9)
    out["ADX"] = dx.rolling(14).mean()
    out["Plus_DI"] = plus_di
    out["Minus_DI"] = minus_di

    # Volume features (if Volume exists)
    if "Volume" in out.columns:
        out["Volume_SMA20"] = out["Volume"].rolling(20).mean()
        out["Volume_ratio"] = out["Volume"] / (out["Volume_SMA20"] + 1e-9)
        out["Volume_std"] = out["Volume"].rolling(20).std()
        # On-Balance Volume
        obv = (np.sign(out["Close"].diff()) * out["Volume"]).fillna(0).cumsum()
        out["OBV"] = obv
        out["OBV_EMA"] = ema(obv, 20)
    else:
        # If no volume, create dummy features
        out["Volume_SMA20"] = 0
        out["Volume_ratio"] = 1
        out["Volume_std"] = 0
        out["OBV"] = 0
        out["OBV_EMA"] = 0

    # Volatility features
    out["HighLow_pct"] = (out["High"] - out["Low"]) / out["Close"]
    out["CloseOpen_pct"] = (out["Close"] - out["Open"]) / out["Open"]
    out["Volatility20"] = out["RET1"].rolling(20).std()
    out["Volatility50"] = out["RET1"].rolling(50).std()

    # Price position features
    out["Close_to_High"] = (out["High"] - out["Close"]) / (out["High"] - out["Low"] + 1e-9)
    out["Close_to_Low"] = (out["Close"] - out["Low"]) / (out["High"] - out["Low"] + 1e-9)

    # Trend features
    out["TrendUp"] = (out["EMA20"] > out["EMA50"]).astype(int)
    out["TrendStrong"] = (out["ADX"] > 25).astype(int)
    out["UpTrend_Confirm"] = ((out["EMA8"] > out["EMA20"]) & (out["EMA20"] > out["EMA50"])).astype(int)
    out["DownTrend_Confirm"] = ((out["EMA8"] < out["EMA20"]) & (out["EMA20"] < out["EMA50"])).astype(int)

    # Candle patterns (simple)
    out["Doji"] = (np.abs(out["Close"] - out["Open"]) <= 0.1 * (out["High"] - out["Low"])).astype(int)
    out["Hammer"] = (((out["High"] - out["Low"]) > 3 * np.abs(out["Close"] - out["Open"])) &
                     ((out["Close"] - out["Low"]) / (out["High"] - out["Low"] + 1e-9) > 0.6)).astype(int)

    # Time-based features (if time column exists)
    if "time" in out.columns:
        out["time"] = pd.to_datetime(out["time"])
        out["Hour"] = out["time"].dt.hour
        out["DayOfWeek"] = out["time"].dt.dayofweek
        out["IsMonday"] = (out["DayOfWeek"] == 0).astype(int)
        out["IsFriday"] = (out["DayOfWeek"] == 4).astype(int)
        # Trading sessions
        out["IsAsianSession"] = ((out["Hour"] >= 0) & (out["Hour"] < 8)).astype(int)
        out["IsLondonSession"] = ((out["Hour"] >= 8) & (out["Hour"] < 16)).astype(int)
        out["IsNYSession"] = ((out["Hour"] >= 13) & (out["Hour"] < 21)).astype(int)

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