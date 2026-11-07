import csv
import datetime

fpath = r'C:\Users\victo\nuevas_ruletas\ledger_nuevas_ruletas.csv'
today = datetime.date.today().strftime('%Y-%m-%d')
rows = []

with open(fpath, encoding='utf-8') as f:
    r = csv.DictReader(f)
    for row in r:
        if str(row.get('fecha', '')).strip() == today:
            rows.append(row)

print(f"Sorteos jugados hoy ({today}): {len(rows)}")
for row in rows:
    print(f"  • {row.get('hora')} | {row.get('ruleta')}")
    print(f"    - Jugados : {row.get('candidatos')}")
    print(f"    - Salió   : {row.get('resultado')}")
    print(f"    - PnL     : ${float(row.get('pnl', 0.0)):+.2f} USD | Saldo: ${float(row.get('saldo', 0.0)):.2f} USD\n")
