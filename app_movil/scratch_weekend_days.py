import os, sys, datetime
import pandas as pd
import numpy as np

sys.path.append(r"C:\Users\victo\nuevas_ruletas")
from bot_nuevas_ruletas import RULETAS_CONFIG, get_history_series

# Mismas operaciones extraídas
from scratch_weekend_audit import events_df

# Análisis de Sharpe, Sortino, PnL por día de la semana
events_df["pnl_net"] = events_df["cobrado"] - events_df["cost"]

dias_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
dias_es = {
    "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
    "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"
}

print("\n--- DESGLOSE DÍA A DÍA (2 AÑOS DE HISTORIAL REAL) ---")
print(f"{'DÍA':<12} | {'OPS':<6} | {'WINS':<5} | {'WR %':<7} | {'INVERSIÓN':<12} | {'COBRADO':<12} | {'PNL NETO':<12} | {'ROI %':<8}")
print("-" * 88)

for d in dias_order:
    sub = events_df[events_df["day_of_week"] == d]
    ops = len(sub)
    wins = sub["hit"].sum()
    wr = (wins / ops * 100.0) if ops > 0 else 0.0
    inv = sub["cost"].sum()
    cob = sub["cobrado"].sum()
    pnl = cob - inv
    roi = (pnl / inv * 100.0) if inv > 0 else 0.0
    print(f"{dias_es[d]:<12} | {ops:<6} | {wins:<5} | {wr:<6.2f}% | ${inv:<10,.2f} | ${cob:<10,.2f} | {'+' if pnl>=0 else ''}${pnl:<10,.2f} | {roi:<+7.2f}%")

# Rendimiento acumulado semanal (Lunes a Viernes vs Sábado a Domingo)
weekday_pnl = events_df[~events_df["is_weekend"]]["pnl_net"].sum()
weekend_pnl = events_df[events_df["is_weekend"]]["pnl_net"].sum()

print("\n--- COMPARATIVA DE RIESGO Y ESTABILIDAD ---")
# Volatilidad diaria del PnL
daily_pnl = events_df.groupby(["fecha", "is_weekend"])["pnl_net"].sum().reset_index()
wd_daily = daily_pnl[~daily_pnl["is_weekend"]]["pnl_net"]
we_daily = daily_pnl[daily_pnl["is_weekend"]]["pnl_net"]

print(f"Lunes a Viernes -> PnL Diario Promedio: +${wd_daily.mean():.2f} USD | Desv. Estándar: ${wd_daily.std():.2f}")
print(f"Fines de Semana -> PnL Diario Promedio: +${we_daily.mean():.2f} USD | Desv. Estándar: ${we_daily.std():.2f}")

# Ratio Sharpe diario anualizado (asumiendo 250 días para LV y 100 días para WE)
sharpe_wd = (wd_daily.mean() / wd_daily.std()) * np.sqrt(250) if wd_daily.std() > 0 else 0
sharpe_we = (we_daily.mean() / we_daily.std()) * np.sqrt(100) if we_daily.std() > 0 else 0
print(f"Ratio Sharpe Anualizado: Lunes a Viernes = {sharpe_wd:.2f} | Fines de Semana = {sharpe_we:.2f}")

# Días en pérdida vs días en ganancia
wd_pos = (wd_daily > 0).sum()
wd_neg = (wd_daily < 0).sum()
we_pos = (we_daily > 0).sum()
we_neg = (we_daily < 0).sum()
print(f"Días ganadores Lunes a Viernes: {wd_pos}/{len(wd_daily)} ({wd_pos/len(wd_daily)*100:.1f}%)")
print(f"Días ganadores Fines de Semana: {we_pos}/{len(we_daily)} ({we_pos/len(we_daily)*100:.1f}%)")
