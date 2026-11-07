import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

with open(r"C:\Users\victo\nuevas_ruletas\ledger_nuevas_ruletas.csv", "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
for i, l in enumerate(lines[-5:]):
    print(f"Line {len(lines)-4+i}: {l.strip()}")
