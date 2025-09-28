from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
import json
import os
import asyncio
from datetime import datetime
import MetaTrader5 as mt5
import yaml

# --- Globals and Configuration ---

app = FastAPI()
g_prices = {}

def load_symbols():
    """Loads symbols from config.yaml"""
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
            return cfg.get("symbols", [])
    except FileNotFoundError:
        print("[WARN] config.yaml not found. No symbols to fetch prices for.")
        return []

# --- Background Task for Price Updates ---

async def price_updater():
    """A background task that connects to MT5 and continuously updates global prices."""
    print("Starting price updater...")
    if not mt5.initialize():
        print("MT5 initialization failed. Price updater will not run.")
        return

    symbols = load_symbols()
    if not symbols:
        print("No symbols configured. Price updater will not run.")
        mt5.shutdown()
        return
        
    print(f"Subscribing to price updates for: {', '.join(symbols)}")
    while True:
        try:
            for symbol in symbols:
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    g_prices[symbol] = {
                        "bid": tick.bid,
                        "ask": tick.ask,
                        "time": datetime.fromtimestamp(tick.time).isoformat(),
                    }
            await asyncio.sleep(1)  # Update every second
        except Exception as e:
            print(f"Error in price updater loop: {e}")
            await asyncio.sleep(10) # Wait longer after an error

@app.on_event("startup")
async def startup_event():
    """On server startup, create the background price updater task."""
    asyncio.create_task(price_updater())

@app.on_event("shutdown")
def shutdown_event():
    """On server shutdown, disconnect from MT5."""
    print("Shutting down MT5 connection.")
    mt5.shutdown()

# --- API Endpoints ---

@app.get("/api/prices")
def api_prices():
    """Returns the latest fetched prices for all symbols."""
    return g_prices

@app.get("/api/signals")
def api_signals():
    """Returns the latest generated trading signals."""
    path = "outputs/signals.json"
    if not os.path.exists(path):
        return {"error": "no signals yet", "signals": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/api/meta-signal")
def api_meta_signal():
    """Returns the latest generated meta-signal."""
    path = "outputs/meta_signal.json"
    if not os.path.exists(path):
        return {"error": "no meta-signal yet"}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# --- HTML Frontend ---

@app.get("/", response_class=HTMLResponse)
def index():
    css = """
    body { background:#111; color:#eee; font:16px/1.5 'Segoe UI', Arial, sans-serif; padding:20px; }
    .card { background:#1a1a1a; border:1px solid #2a2a2a; border-radius:12px; padding:16px; margin:12px 0; }
    h1, h2 { margin-top:0; color:#f2f2f2; font-weight: 300; }
    h1 { font-size: 36px; }
    h2 { font-size: 24px; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; }
    .refresh-btn { background: #333; border: 1px solid #555; color: #eee; padding: 5px 10px; border-radius: 6px; cursor: pointer; font-size: 14px; }
    .refresh-btn:hover { background: #444; }
    table { width:100%; border-collapse:collapse; margin-top: 10px; }
    th, td { padding:8px; border-bottom:1px solid #2a2a2a; text-align:left; }
    th { text-transform:uppercase; font-size:12px; letter-spacing:0.08em; color:#bdbdbd; }
    .long { color:#4caf50; font-weight:bold; }
    .short { color:#f44336; font-weight:bold; }
    .watch { color:#ff9800; font-weight:bold; }
    .meta { color:#9a9a9a; font-size:12px; margin-top:6px; }
    .info-bar { padding: 10px; background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px; margin-bottom: 20px; font-size: 14px; }
    .ideas tbody tr:nth-child(2) { background:#151515; }
    #price-table th, #price-table td { text-align: right; }
    #price-table th:first-child, #price-table td:first-child { text-align: left; }
    #meta-signal-summary { background: linear-gradient(45deg, #2a2a2a, #1a1a1a); border: 1px solid #444; border-radius: 16px; padding: 25px; text-align: center; margin-bottom: 20px; }
    #meta-signal-summary .recommendation { font-size: 28px; font-weight: bold; margin: 10px 0; letter-spacing: 1px; }
    #meta-signal-summary .details { font-size: 14px; color: #bdbdbd; }
    .main-flex-container { display: flex; gap: 20px; align-items: flex-start; }
    .left-column { flex: 1; min-width: 300px; }
    .right-column { flex: 2; min-width: 600px; }
    """

    js = """
    const fmtPct = (value) => `${(value * 100).toFixed(1)}%`;
    const fmtPct4 = (value) => `${(value * 100).toFixed(4)}%`;

    function formatFilters(decision) {
      const filters = [];
      filters.push(decision.probability_pass ? 'ймовірність ✔' : 'ймовірність ✖');
      filters.push(decision.trend_pass ? 'тренд ✔' : 'тренд ✖');
      return filters.join(', ');
    }

    async function loadMetaSignal() {
        const response = await fetch('/api/meta-signal');
        const meta = await response.json();
        const container = document.getElementById('meta-signal-summary');
        let html = `<h2>Головний Сигнал<button id="refresh-meta-btn" class="refresh-btn">🔄</button></h2>`;
        
        if (meta.error) {
            html += `<div class="details">Очікуємо на генерацію...</div>`;
        } else {
            html += `<div class="recommendation long">LONG ${meta.recommended_pair}</div>`;
            html += `<div class="details">Найсильніша: <strong>${meta.strongest_currency}</strong> (прогноз: ${fmtPct4(meta.strongest_prediction)}) | Найслабша: <strong>${meta.weakest_currency}</strong> (прогноз: ${fmtPct4(meta.weakest_prediction)})</div>`;
            
            if (meta.trade_levels) {
                html += `<table class="ideas"><thead><tr><th>Тип</th><th>Entry</th><th>SL</th><th>TP1</th><th>TP2</th></tr></thead><tbody>`;
                html += `<tr><td>Meta</td><td>${meta.trade_levels.entry}</td><td>${meta.trade_levels.sl}</td><td>${meta.trade_levels.tp1}</td><td>${meta.trade_levels.tp2}</td></tr>`;
                html += `</tbody></table>`;
            }
            html += `<div class="meta">Згенеровано: ${new Date(meta.generated_at).toLocaleString()}</div>`;
        }
        container.innerHTML = html;
    }

    async function loadPrices() {
        const response = await fetch('/api/prices');
        const prices = await response.json();
        const tableBody = document.getElementById('price-table-body');
        tableBody.innerHTML = '';
        for (const symbol in prices) {
            const price = prices[symbol];
            const row = `<tr><td>${symbol}</td><td>${price.bid}</td><td>${price.ask}</td><td>${new Date(price.time).toLocaleTimeString()}</td></tr>`;
            tableBody.innerHTML += row;
        }
    }

    async function loadSignals() {
      const response = await fetch('/api/signals');
      const payload = await response.json();
      const container = document.getElementById('signals');
      const generatedAt = document.getElementById('generated_at');
      
      generatedAt.textContent = payload.generated_at ? `Останнє оновлення сигналів: ${new Date(payload.generated_at).toLocaleString()}` : 'Сигнали ще не згенеровано.';
      container.innerHTML = '';

      if (payload.signals && payload.signals.length) {
        for (const item of payload.signals) {
          const { decision, primary, alternative, trend_up, probabilities } = item.signal;
          const sideClass = decision.side === 'LONG' ? 'long' : 'short';
          const statusClass = decision.status === 'ACTIVE' ? sideClass : 'watch';
          const card = document.createElement('div');
          card.className = 'card';

          let body = `<h2>${item.symbol} ${item.tf} -> <span class="${sideClass}">${decision.side}</span></h2>`;
          body += `<div class="meta">Статус: <span class="${statusClass}">${decision.status}</span> | Фільтри: ${formatFilters(decision)}</div>`;
          body += `<div class="meta">Коментар: ${decision.comment} (впевненість ${fmtPct(decision.confidence)})</div>`;

          body += '<table class="ideas"><thead><tr><th>Тип</th><th>Сторона</th><th>Entry</th><th>SL</th><th>TP1</th><th>TP2</th><th>Впевненість</th></tr></thead><tbody>';
          body += `<tr><td>Primary</td><td>${primary.side}</td><td>${primary.entry}</td><td>${primary.sl}</td><td>${primary.tp1}</td><td>${primary.tp2}</td><td>${fmtPct(primary.confidence)}</td></tr>`;
          body += `<tr><td>Alternative</td><td>${alternative.side}</td><td>${alternative.entry}</td><td>${alternative.sl}</td><td>${alternative.tp1}</td><td>${alternative.tp2}</td><td>${fmtPct(alternative.confidence)}</td></tr>`;
          body += '</tbody></table>';

          body += `<div class="meta">Тренд: ${trend_up ? 'UP' : 'DOWN'} | Ймовірності → Long ${fmtPct(probabilities.long)}, No ${fmtPct(probabilities.no)}, Short ${fmtPct(probabilities.short)}</div>`;
          body += `<div class="meta">Згенеровано: ${new Date(item.time).toLocaleString()}</div>`;

          card.innerHTML = body;
          container.appendChild(card);
        }
      } else {
        container.innerHTML = '<div class="card">Сигнали з\\'являться після запуску автоматичного оновлення за розкладом.</div>';
      }
    }
    
    window.addEventListener('load', () => {
        loadMetaSignal();
        loadSignals();
        loadPrices();
        setInterval(loadMetaSignal, 60000);
        setInterval(loadSignals, 60000);
        setInterval(loadPrices, 1000);

        // Use event delegation on a static parent element
        document.getElementById('meta-signal-summary').addEventListener('click', (event) => {
            if (event.target.id === 'refresh-meta-btn') {
                loadMetaSignal();
            }
        });
        document.getElementById('signal-section-header').addEventListener('click', (event) => {
            if (event.target.id === 'refresh-signals-btn') {
                loadSignals();
            }
        });
    });
    """

    html = (
        '<html><head><meta charset="utf-8"><title>Forex LSTM Signals</title><style>'
        + css
        + '</style></head>'
        '<body>'
        '<h1>Forex LSTM Dashboard</h1>'
        '<div class="info-bar">'
        'Сигнали оновлюються автоматично за розкладом. Ціни оновлюються в реальному часі.'
        '<div id="generated_at"></div>'
        '</div>'
        '<div class="main-flex-container">'
        '<div class="left-column">'
        '<div id="meta-signal-summary" class="card"></div>'
        '<div class="price-section card">'
        '<h2>Ціни в реальному часі</h2>'
        '<table id="price-table"><thead><tr><th>Символ</th><th>Bid</th><th>Ask</th><th>Час</th></tr></thead><tbody id="price-table-body"></tbody></table>'
        '</div>'
        '</div>'
        '<div class="right-column">'
        '<div class="signal-section">'
        '<h2 id="signal-section-header">Торгові сигнали<button id="refresh-signals-btn" class="refresh-btn">🔄</button></h2>'
        '<div id="signals"></div>'
        '</div>'
        '</div>'
        '</div>'
        '<script>'
        + js
        + '</script>'
        '</body></html>'
    )
    return HTMLResponse(html)
