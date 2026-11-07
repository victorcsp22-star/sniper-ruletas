import csv
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

with open(r"C:\Users\victo\nuevas_ruletas\ledger_nuevas_ruletas.csv.base_backup", "r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    for r in reader:
        if r.get("ruleta") == "Ruleta Royal" and "2026-10-27" in r.get("fecha", ""):
            print(f"Base RR: {r.get('fecha')} {r.get('hora')} | Res: {r.get('resultado')} | Cond: {r.get('condicion')} | PnL: ${r.get('pnl')} | Saldo: ${r.get('saldo')}")
