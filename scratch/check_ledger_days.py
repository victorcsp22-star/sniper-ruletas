import csv
import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = r"C:\Users\victo\nuevas_ruletas"

def load_ledger(filepath):
    rows = []
    if not os.path.exists(filepath):
        return rows
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows

base_ledger = load_ledger(os.path.join(ROOT_DIR, "ledger_nuevas_ruletas.csv.base_backup"))
max_ledger = load_ledger(os.path.join(ROOT_DIR, "ledger_nuevas_ruletas.csv"))

print(f"Base ledger rows: {len(base_ledger)}")
print(f"Max ledger rows: {len(max_ledger)}")

# Group base by day
from collections import defaultdict
days_base = defaultdict(list)
for r in base_ledger:
    days_base[r.get("fecha", "").strip()].append(r)

print("\n--- BASE LEDGER DIAS ---")
for d, rows in sorted(days_base.items()):
    wins = sum(1 for r in rows if "GANADA" in r.get("condicion", ""))
    inv = sum(float(r.get("total_bet", 0) or 0) for r in rows)
    pnl = sum(float(r.get("pnl", 0) or 0) for r in rows)
    print(f"Fecha: {d:<12} | Operaciones: {len(rows):>2} | Aciertos: {wins} | Invertido: ${inv:>6.2f} | PnL: ${pnl:>+6.2f}")

days_max = defaultdict(list)
for r in max_ledger:
    days_max[r.get("fecha", "").strip()].append(r)

print("\n--- MAX LEDGER DIAS ---")
for d, rows in sorted(days_max.items()):
    wins = sum(1 for r in rows if "GANADA" in r.get("condicion", ""))
    inv = sum(float(r.get("total_bet", 0) or 0) for r in rows)
    pnl = sum(float(r.get("pnl", 0) or 0) for r in rows)
    print(f"Fecha: {d:<12} | Operaciones: {len(rows):>2} | Aciertos: {wins} | Invertido: ${inv:>6.2f} | PnL: ${pnl:>+6.2f}")
