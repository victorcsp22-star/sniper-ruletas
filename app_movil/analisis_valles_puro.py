import os, sys
import pandas as pd

sys.path.append(r"C:\Users\victo\nuevas_ruletas")
import bot_nuevas_ruletas as bot
from test_pure_bot_master import df_ev

# Analizar rachas de fallos en df_ev
def parse_time(h_str):
    try:
        import datetime
        return datetime.datetime.strptime(str(h_str).strip(), "%I:%M %p").time()
    except Exception:
        import datetime
        return datetime.time(0, 0)

df_ev['hora_t'] = df_ev['hora'].apply(parse_time)
df_ev = df_ev.sort_values(by=['fecha', 'hora_t']).reset_index(drop=True)

# Contar rachas de fallos consecutivas
streaks = []
cur_streak = 0
for hit in df_ev['hit']:
    if hit:
        streaks.append(cur_streak)
        cur_streak = 0
    else:
        cur_streak += 1
streaks.append(cur_streak)

print(f"Total valles de fallos registrados: {len(streaks)}")
print(f"Valle promedio: {sum(streaks)/len(streaks):.1f} fallos seguidos")
print(f"Mediana: {pd.Series(streaks).median():.1f}")
print(f"Máximo histórico de fallos seguidos: {max(streaks)}")
print(f"Racha actual al cierre de hoy: {cur_streak} fallos seguidos")
