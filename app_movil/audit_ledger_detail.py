import pandas as pd

df = pd.read_csv(r'C:\Users\victo\nuevas_ruletas\app_movil\ledger_nuevas_ruletas.csv')
print("=== TODAS LAS JUGADAS REGISTRADAS EN EL CICLO ===")
for idx, r in df.iterrows():
    print(f"[{r['fecha']} {r['hora']}] {r['ruleta']} -> Apostado a: {r['candidatos']} ({r['cands_count']} f.) | Salio: {r['resultado']} | Cond: {r['condicion']} | PnL: Bs {r['pnl']}")
