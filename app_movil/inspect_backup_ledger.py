import pandas as pd

l = r"C:\Users\victo\nuevas_ruletas\ledger_nuevas_ruletas_backup_3meses.csv"
df = pd.read_csv(l)
print("Backup 3 meses:")
print("Columnas:", list(df.columns))
print("Fechas tail:", df['fecha'].tail(20).tolist())
oct_nov = df[df['fecha'] >= '2026-10-25']
print(f"Filas desde 2026-10-25: {len(oct_nov)}")
for idx, r in oct_nov.iterrows():
    print(f"[{r['fecha']} {r.get('hora', '')}] {r.get('ruleta', '')} -> {r.get('condicion', '')} | PnL: {r.get('pnl', '')}")
