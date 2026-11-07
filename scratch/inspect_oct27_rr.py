import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

with open(r"C:\Users\victo\nuevas_ruletas\scratch\replay_with_auditors_summary.json", "r", encoding="utf-8") as f:
    data = json.load(f)

trades = data["trades"]
rr_trades = [t for t in trades if t["ruleta"] == "Ruleta Royal" and "2026-10-27" in t["fecha"]]
print(f"Ruleta Royal trades on Oct 27 in MAX ({len(rr_trades)}):")
for t in rr_trades:
    print(f"• {t['fecha']} {t['hora']} | Salido: {t['resultado']} | Cond: {t['condicion']} | PnL: ${t['pnl']} | Saldo: ${t['saldo']}")
