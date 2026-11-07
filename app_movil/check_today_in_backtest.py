import pandas as pd

# Verificar el día 2026-11-02 en backtest_exacto_app.py
from backtest_exacto_app import run_exact_backtest

df_all = run_exact_backtest()
hoy = df_all[df_all['fecha'] == '2026-11-02']
print("=== TODAS LAS OPERACIONES QUE EL MOTOR DE LA APP REGISTRÓ HOY (2026-11-02) ===")
print(f"Total: {len(hoy)}")
for idx, r in hoy.iterrows():
    print(f"[{r['hora']}] {r['ruleta']} ({r['tipo']}) -> Cands: {r['cands']} | Salió: #{r['actual']} | Hit: {r['hit']} | PnL: {r['pnl']}")
