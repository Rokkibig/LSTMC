from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import os
import json
from datetime import datetime
import requests

app = FastAPI(title="LSTM Forex Signals API")

SIGNALS_FILE = "/home/aiagent1/LSTMC/outputs/signals.json"
META_SIGNAL_FILE = "/home/aiagent1/LSTMC/outputs/meta_signal.json"
WINDOWS_API = os.getenv("WINDOWS_API", "http://84.247.166.52:8000")

@app.get("/api/signals")
def get_signals():
    if os.path.exists(SIGNALS_FILE):
        with open(SIGNALS_FILE) as f:
            data = json.load(f)
        return data
    return {"error": "no signals yet", "signals": []}

@app.get("/api/meta-signal")
def get_meta_signal():
    if os.path.exists(META_SIGNAL_FILE):
        with open(META_SIGNAL_FILE) as f:
            data = json.load(f)
        return data
    return {"error": "no meta-signal yet"}

@app.get("/api/prices")
def get_prices():
    """Proxy real-time prices from Windows server"""
    try:
        response = requests.get(f"{WINDOWS_API}/api/prices", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"error": "Windows API unavailable"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/health")
def health():
    signals_exist = os.path.exists(SIGNALS_FILE)
    if signals_exist:
        mtime = os.path.getmtime(SIGNALS_FILE)
        updated = datetime.fromtimestamp(mtime).isoformat()
    else:
        updated = None

    return {
        "status": "ok",
        "signals_available": signals_exist,
        "last_update": updated
    }

@app.get("/", response_class=HTMLResponse)
def index():
    css = """
    body { background:#111; color:#eee; font:16px/1.5 'Segoe UI', Arial, sans-serif; padding:20px; }
    .card { background:#1a1a1a; border:1px solid #2a2a2a; border-radius:12px; padding:16px; margin:12px 0; }
    h1, h2 { margin-top:0; color:#f2f2f2; font-weight: 300; }
    h1 { font-size: 36px; }
    h2 { font-size: 24px; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 15px; }
    table { width:100%; border-collapse:collapse; margin-top: 10px; }
    th, td { padding:8px; border-bottom:1px solid #2a2a2a; text-align:left; }
    th { text-transform:uppercase; font-size:12px; letter-spacing:0.08em; color:#bdbdbd; }
    .long { color:#4caf50; font-weight:bold; }
    .short { color:#f44336; font-weight:bold; }
    .watch { color:#ff9800; font-weight:bold; }
    .meta { color:#9a9a9a; font-size:12px; margin-top:6px; }
    .info-bar { padding: 10px; background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px; margin-bottom: 20px; font-size: 14px; }
    #meta-signal-summary { background: linear-gradient(45deg, #2a2a2a, #1a1a1a); border: 1px solid #444; border-radius: 16px; padding: 25px; text-align: center; margin-bottom: 20px; }
    #meta-signal-summary .recommendation { font-size: 28px; font-weight: bold; margin: 10px 0; letter-spacing: 1px; }
    #meta-signal-summary .details { font-size: 14px; color: #bdbdbd; }
    #price-table th, #price-table td { text-align: right; }
    #price-table th:first-child, #price-table td:first-child { text-align: left; }
    .main-flex { display: flex; gap: 20px; }
    .left-col { flex: 1; min-width: 300px; }
    .right-col { flex: 2; min-width: 500px; }
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
        let html = `<h2>Головний Сигнал</h2>`;

        if (meta.error) {
            html += `<div class="details">${meta.error}</div>`;
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
        container.innerHTML = '<div class="card">Сигнали з\\'являться після завантаження signals.json з Windows.</div>';
      }
    }

    async function loadPrices() {
        const response = await fetch('/api/prices');
        const prices = await response.json();
        const tableBody = document.getElementById('price-table-body');

        if (prices.error) {
            tableBody.innerHTML = `<tr><td colspan="4" style="text-align:center;color:#f44336;">${prices.error}</td></tr>`;
            return;
        }

        tableBody.innerHTML = '';
        for (const symbol in prices) {
            const price = prices[symbol];
            const row = `<tr><td>${symbol}</td><td>${price.bid.toFixed(5)}</td><td>${price.ask.toFixed(5)}</td><td>${new Date(price.time).toLocaleTimeString()}</td></tr>`;
            tableBody.innerHTML += row;
        }
    }

    window.addEventListener('load', () => {
        loadMetaSignal();
        loadSignals();
        loadPrices();
        setInterval(loadMetaSignal, 60000);
        setInterval(loadSignals, 60000);
        setInterval(loadPrices, 2000);
    });
    """

    html = (
        '<html><head><meta charset="utf-8"><title>Forex LSTM Signals</title><style>'
        + css
        + '</style></head>'
        '<body>'
        '<h1>Forex LSTM Dashboard (Linux)</h1>'
        '<div class="info-bar">'
        'Панель оновлюється автоматично. Сигнали генеруються на Windows і синхронізуються на Linux. Ціни в реальному часі з Windows MT5.'
        '<div id="generated_at"></div>'
        '</div>'
        '<div class="main-flex">'
        '<div class="left-col">'
        '<div id="meta-signal-summary" class="card">Завантаження...</div>'
        '<div class="price-section card">'
        '<h2>Ціни в реальному часі</h2>'
        '<table id="price-table"><thead><tr><th>Символ</th><th>Bid</th><th>Ask</th><th>Час</th></tr></thead><tbody id="price-table-body"></tbody></table>'
        '</div>'
        '</div>'
        '<div class="right-col">'
        '<div class="signal-section">'
        '<h2>Торгові сигнали</h2>'
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
