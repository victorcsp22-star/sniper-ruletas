import json, collections
import pandas as pd

# Distribución exacta de la duración de las rachas de pérdida
with open(r"C:\Users\victo\nuevas_ruletas\scratch\analizar_dias_semanas_perdidas.py") as f:
    pass

# Re-calcular distribución exacta
import sys
sys.path.append(r"C:\Users\victo\nuevas_ruletas\scratch")
from analizar_dias_semanas_perdidas import daily_plana, daily_pesos

def get_streak_dist(d_dict):
    days = sorted(d_dict.keys())
    pnls = [d_dict[d]["cob"] - d_dict[d]["inv"] for d in days]
    loss_streaks = []
    c = 0
    for p in pnls:
        if p < 0: c += 1
        else:
            if c > 0: loss_streaks.append(c)
            c = 0
    if c > 0: loss_streaks.append(c)
    return collections.Counter(loss_streaks)

c_p = get_streak_dist(daily_plana)
c_w = get_streak_dist(daily_pesos)

print("Distribución de rachas de DÍAS perdedores seguidos:")
print(f"{'DÍAS SEGUIDOS':<15} | {'PLANA ($1)':<12} | {'PESOS (1-10)'}")
for d in range(1, 15):
    print(f"{d:>2} días seguidos  | {c_p.get(d, 0):>6} veces   | {c_w.get(d, 0):>6} veces")
