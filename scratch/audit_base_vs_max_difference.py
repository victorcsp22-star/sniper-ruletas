import csv
import sys
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Read base ledger
base_rows = []
with open(r"C:\Users\victo\nuevas_ruletas\ledger_nuevas_ruletas.csv.base_backup", "r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    for row in reader:
        base_rows.append(row)

# Read max ledger
max_rows = []
with open(r"C:\Users\victo\nuevas_ruletas\ledger_nuevas_ruletas.csv", "r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    for row in reader:
        max_rows.append(row)

print(f"Base Total Trades: {len(base_rows)}")
print(f"Max Total Trades: {len(max_rows)}")

base_wins = [r for r in base_rows if "GANADA" in r.get("condicion", "")]
max_wins = [r for r in max_rows if "GANADA" in r.get("condicion", "")]

print(f"\n--- BASE WINS ({len(base_wins)}) ---")
for w in base_wins:
    print(f"• {w.get('fecha')} {w.get('hora')} | {w.get('ruleta')} | Salido: {w.get('resultado')} | Bet: ${w.get('total_bet')} | PnL: ${w.get('pnl')} | Saldo: ${w.get('saldo')}")

print(f"\n--- MAX WINS ({len(max_wins)}) ---")
for w in max_wins:
    print(f"• {w.get('fecha')} {w.get('hora')} | {w.get('ruleta')} | Salido: {w.get('resultado')} | Bet: ${w.get('total_bet')} | PnL: ${w.get('pnl')} | Saldo: ${w.get('saldo')}")

# Identify which win is in Base that is missing in Max, or vice versa
base_win_keys = {(w.get('fecha'), w.get('hora'), w.get('ruleta')): w for w in base_wins}
max_win_keys = {(w.get('fecha'), w.get('hora'), w.get('ruleta')): w for w in max_wins}

missing_in_max = set(base_win_keys.keys()) - set(max_win_keys.keys())
extra_in_max = set(max_win_keys.keys()) - set(base_win_keys.keys())

print(f"\n--- WINS PRESENTES EN BASE PERO AUSENTES EN MAX ({len(missing_in_max)}) ---")
for k in missing_in_max:
    print(f"❌ {k}: {base_win_keys[k]}")

print(f"\n--- WINS PRESENTES EN MAX PERO AUSENTES EN BASE ({len(extra_in_max)}) ---")
for k in extra_in_max:
    print(f"⭐ {k}: {max_win_keys[k]}")
