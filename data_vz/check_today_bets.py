import pandas as pd
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

for name, fname in [("VENEZUELA", "production_ledger_venezuela.csv"), ("BRASIL", "production_ledger_brasil.csv")]:
    df = pd.read_csv(fname)
    today = df[df['fecha'] == '2026-10-14']
    print(f"\n=== DISPAROS EJECUTADOS HOY EN {name} (2026-10-14) ===")
    if not today.empty:
        for _, row in today.iterrows():
            hit_str = "GANADA (+$$$)" if row["acierto"] == 1 else "Perdida"
            print(f"  [{row['hora']:>8}] {row['ruleta']:<15} | Cands: {row['candidatos']} | Salió: {row['resultado_num']} ({row['resultado_animal']}) | {hit_str} | PnL: ${row['pnl']:+.2f} | Balance: ${row['balance_cierre']:,.2f}")
    else:
        print("  Sin disparos ejecutados hoy.")
