from pathlib import Path
import json
text = Path('outputs/signals.json').read_text(encoding='utf-8')
data = json.loads(text)
comment = data['signals'][0]['signal']['decision']['comment']
print(comment)
print([ord(ch) for ch in comment[:10]])
