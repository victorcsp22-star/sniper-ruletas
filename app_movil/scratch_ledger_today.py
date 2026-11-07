import csv, json

ledger_file = r"C:\Users\victo\nuevas_ruletas\ledger_nuevas_ruletas.csv"
today = "2026-11-01"

with open(ledger_file, "r", encoding="utf-8", errors="ignore") as f:
    reader = csv.DictReader(f)
    rows = [r for r in reader if r.get("fecha") == today]

print(f"Total operaciones hoy ({today}): {len(rows)}")
for r in rows:
    hora = r.get("hora")
    rul = r.get("ruleta")
    cands = r.get("candidatos")
    cc = r.get("cands_count")
    res = r.get("resultado")
    bet = r.get("total_bet")
    cob = r.get("cobrado")
    pnl = r.get("pnl")
    sal = r.get("saldo")
    print(f"Hora: {hora:<9} | {rul:<26} | Jugados: {cands} ({cc} cands) | Salido: {res:<18} | Bet: ${bet} | Cob: ${cob} | PnL: ${pnl} | Saldo: ${sal}")
