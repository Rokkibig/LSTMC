import json
from pathlib import Path
signals = json.loads(Path('outputs/signals.json').read_text(encoding='utf-8'))['signals']
active = [s for s in signals if s['signal']['decision']['status'] == 'ACTIVE']
print('Активних сигналів:', len(active))
for s in active[:5]:
    d = s['signal']['decision']
    print(f"{s['symbol']} {s['tf']} -> {d['side']} (впевненість {d['confidence']:.2f})")
