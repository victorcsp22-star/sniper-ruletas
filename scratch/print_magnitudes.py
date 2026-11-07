import sys
sys.path.append(r'C:\Users\victo\nuevas_ruletas')
from scratch.analyze_2y_daily_streaks import df_days

wins = df_days[df_days['state'] == 'W']['pnl']
losses = df_days[df_days['state'] == 'L']['pnl']

print("="*60)
print(f"Ganancia Promedio en Día Ganador: +{wins.mean():.2f} USD")
print(f"Ganancia Máxima en 1 solo Día   : +{wins.max():.2f} USD")
print(f"Pérdida Promedio en Día Perdedor: -{abs(losses.mean()):.2f} USD")
print(f"Pérdida Máxima en 1 solo Día    : -{abs(losses.min()):.2f} USD")
print(f"Ratio de Asimetría (Win/Loss)   : {wins.mean() / abs(losses.mean()):.2f} a favor")
print(f"PnL Neto Total en 2 Años        : +{df_days['pnl'].sum():.2f} USD")
print("="*60)
