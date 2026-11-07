import pandas as pd

df = pd.read_csv(r'C:\Users\victo\nuevas_ruletas\app_movil\ledger_nuevas_ruletas.csv')
print("=== TODAS LAS JUGADAS DEL CICLO CON DISPERSION ===")
for idx, r in df.iterrows():
    payout = 60.0 if any(k in str(r['ruleta']) for k in ['Guacharo', 'Granja', 'Gatazo', 'Lotto Gato', 'Monje']) else 30.0
    print(f"[{r['fecha']} {r['hora']}] {r['ruleta']} ({payout}x) | Apuesta: {r['cands_count']} fichas (Bs {r['total_bet']}) | Candidatos: {r['candidatos']} | Salio: {r['resultado']}")
