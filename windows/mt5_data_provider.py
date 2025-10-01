"""
MT5 Data Provider - Simple API for Linux Server
Provides real-time and historical data from MetaTrader 5
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd
import yaml

app = Flask(__name__)
CORS(app)  # Allow requests from Linux server

# Global config
CONFIG = None


def load_config():
    """Load configuration"""
    global CONFIG
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            CONFIG = yaml.safe_load(f)
    except Exception as e:
        print(f"Failed to load config: {e}")
        CONFIG = {"symbols": ["EURUSD", "GBPUSD", "USDJPY"]}


def init_mt5():
    """Initialize MT5 connection"""
    if not mt5.initialize():
        print("MT5 initialization failed!")
        return False
    print(f"MT5 initialized. Terminal: {mt5.terminal_info()}")
    return True


@app.route("/")
def index():
    """Health check"""
    return jsonify({
        "service": "MT5 Data Provider",
        "status": "running",
        "mt5_connected": mt5.terminal_info() is not None,
        "version": "1.0"
    })


@app.route("/api/mt5/health")
def health():
    """MT5 connection health"""
    terminal_info = mt5.terminal_info()
    if terminal_info is None:
        return jsonify({"status": "error", "message": "MT5 not connected"}), 503

    return jsonify({
        "status": "ok",
        "connected": True,
        "terminal": terminal_info.company,
        "build": terminal_info.build
    })


@app.route("/api/mt5/price/<symbol>")
def get_price(symbol):
    """Get current price for symbol"""
    symbol = symbol.upper()

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return jsonify({"error": f"Failed to get tick for {symbol}"}), 404

    return jsonify({
        "symbol": symbol,
        "bid": tick.bid,
        "ask": tick.ask,
        "last": tick.last,
        "volume": tick.volume,
        "time": datetime.fromtimestamp(tick.time).isoformat(),
        "spread": tick.ask - tick.bid,
        "timestamp": datetime.now().isoformat()
    })


@app.route("/api/mt5/prices")
def get_all_prices():
    """Get prices for all configured symbols"""
    if CONFIG is None:
        load_config()

    symbols = CONFIG.get("symbols", [])
    prices = []

    for symbol in symbols:
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            prices.append({
                "symbol": symbol,
                "bid": tick.bid,
                "ask": tick.ask,
                "last": tick.last,
                "time": datetime.fromtimestamp(tick.time).isoformat(),
                "spread": tick.ask - tick.bid
            })

    return jsonify({
        "prices": prices,
        "count": len(prices),
        "timestamp": datetime.now().isoformat()
    })


@app.route("/api/mt5/history/<symbol>/<timeframe>")
def get_history(symbol, timeframe):
    """
    Get historical data for symbol

    Query params:
    - years: number of years of history (default: 1)
    - limit: max number of bars (default: 10000)

    Example: /api/mt5/history/EURUSD/H1?years=2
    """
    symbol = symbol.upper()
    years = int(request.args.get("years", 1))
    limit = int(request.args.get("limit", 10000))

    # Map timeframe string to MT5 constant
    tf_map = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H2": mt5.TIMEFRAME_H2,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
        "W1": mt5.TIMEFRAME_W1,
        "MN1": mt5.TIMEFRAME_MN1,
    }

    if timeframe not in tf_map:
        return jsonify({"error": f"Invalid timeframe: {timeframe}"}), 400

    mt5_tf = tf_map[timeframe]

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * years)

    # Fetch data
    rates = mt5.copy_rates_range(symbol, mt5_tf, start_date, end_date)

    if rates is None or len(rates) == 0:
        return jsonify({"error": f"Failed to get data for {symbol} {timeframe}"}), 404

    # Convert to DataFrame
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")

    # Limit number of bars
    if len(df) > limit:
        df = df.tail(limit)

    # Convert to records
    records = df.to_dict(orient="records")

    # Format timestamps
    for record in records:
        record["time"] = record["time"].isoformat()

    return jsonify({
        "symbol": symbol,
        "timeframe": timeframe,
        "years": years,
        "bars_count": len(records),
        "start_date": records[0]["time"] if records else None,
        "end_date": records[-1]["time"] if records else None,
        "data": records
    })


@app.route("/api/mt5/symbols")
def get_symbols():
    """Get list of available symbols"""
    if CONFIG is None:
        load_config()

    symbols = CONFIG.get("symbols", [])
    symbol_info = []

    for symbol in symbols:
        info = mt5.symbol_info(symbol)
        if info:
            symbol_info.append({
                "symbol": symbol,
                "description": info.description,
                "digits": info.digits,
                "point": info.point,
                "spread": info.spread,
                "trade_mode": info.trade_mode,
                "visible": info.visible
            })

    return jsonify({
        "symbols": symbol_info,
        "count": len(symbol_info)
    })


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    print("=" * 60)
    print("  MT5 Data Provider API")
    print("  Provides data for Linux ML Server")
    print("=" * 60)

    # Load config
    load_config()

    # Initialize MT5
    if not init_mt5():
        print("ERROR: MT5 not initialized. Please start MT5 Terminal!")
        exit(1)

    print("\nAPI Endpoints:")
    print("  GET /                          - Health check")
    print("  GET /api/mt5/health            - MT5 connection status")
    print("  GET /api/mt5/price/{symbol}    - Current price")
    print("  GET /api/mt5/prices            - All prices")
    print("  GET /api/mt5/history/{symbol}/{tf}?years=N")
    print("  GET /api/mt5/symbols           - Available symbols")
    print("\nStarting server on http://0.0.0.0:5000")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    try:
        app.run(host="0.0.0.0", port=5000, debug=False)
    finally:
        mt5.shutdown()
        print("\nMT5 connection closed.")
