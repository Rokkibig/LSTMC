from pathlib import Path
text = Path('scripts/infer_signals.py').read_text(encoding='utf-8')
for line in text.splitlines():
    if 'issues.append' in line:
        print(line)
        print(list(map(ord, line)))
        break
