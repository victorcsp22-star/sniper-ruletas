import csv
import sys
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

cols_16 = [
    "fecha", "hora", "ruleta", "candidatos", "cands_count", "zona_patron",
    "smart_mult", "stake_unit", "total_bet", "resultado", "condicion",
    "cobrado", "pnl", "saldo", "peak", "drawdown_pct"
]

rows = []
with open(r"C:\Users\victo\nuevas_ruletas\ledger_nuevas_ruletas.csv", "r", encoding="utf-8", errors="replace") as f:
    reader = csv.reader(f)
    header = next(reader)
    for r in reader:
        if not r:
            continue
        if len(r) == 15:
            # Insert smart_mult at index 6
            r_fixed = r[:6] + ["1.0"] + r[6:]
            rows.append(r_fixed)
        elif len(r) == 16:
            rows.append(r)
        else:
            print("Row with odd length:", len(r), r)

df_fixed = pd.DataFrame(rows, columns=cols_16)
df_fixed.to_csv(r"C:\Users\victo\nuevas_ruletas\ledger_nuevas_ruletas.csv", index=False, encoding="utf-8")
print(f"Fixed ledger saved with {len(df_fixed)} rows and exactly 16 columns!")
