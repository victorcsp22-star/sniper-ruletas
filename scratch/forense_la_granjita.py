"""
Diagnóstico Forense Profundo de La Granjita (8,844 sorteos).
Investiga:
1. Rendimiento por hora exacta del día (sesión mañana vs tarde vs noche).
2. Tasa de repetición intradía (clustering) y lag 1 (repetición inmediata).
3. Rendimiento en cada racha (0, 1, 2, 3, 4, 5, 6-10, 11-20, 21+).
4. Grid search de lags: ¿estamos usando los lags correctos [15, 17] o hay otros mejores?
5. Matriz de Markov: ¿existen pares deterministas en La Granjita?
6. Anomalías por día de la semana.
7. Veredicto de seguridad institucional: ¿Se debe mantener o reemplazar en el top 10?
"""

import os, collections, datetime
import pandas as pd
import numpy as np

FPATH = r"C:\Users\victo\nuevas_ruletas\data_vz\la_granjita_2anios.csv"
df = pd.read_csv(FPATH)

# Asegurar orden cronológico
df["dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], errors="coerce")
df = df.sort_values(by="dt").dropna(subset=["numero"]).reset_index(drop=True)

nums = [str(x).strip() for x in df["numero"].tolist()]
horas = [str(x).strip() for x in df["hora"].tolist()]
fechas = [str(x).strip() for x in df["fecha"].tolist()]
dias = [str(x).strip() for x in df["dia"].tolist()] if "dia" in df.columns else [""] * len(nums)
N = len(nums)
payout = 30.0

print(f"=== DIAGNÓSTICO FORENSE: LA GRANJITA ({N} sorteos) ===")

# 1. EVALUAR LAGS DEL 1 AL 60
print("\n--- 1. ESCANEO GLOBAL DE LAGS (Top 10 por lift estadístico) ---")
p_rand = 1.0 / 38.0
lag_stats = []
for l in range(1, 60):
    hits = sum(1 for i in range(l, N) if nums[i] == nums[i-l])
    trials = N - l
    rate = hits / trials if trials > 0 else 0
    lift = rate / p_rand
    lag_stats.append((l, hits, trials, rate * 100, lift))

lag_stats.sort(key=lambda x: x[4], reverse=True)
for l, h, tr, r, lift in lag_stats[:10]:
    print(f"  Lag {l:>2}: {h:>4}/{tr} aciertos ({r:>5.2f}%) | Lift: {lift:.2f}x")

# Comparar con los lags actuales del bot: [15, 17]
lag_dict = {x[0]: x for x in lag_stats}
print("\n  Lags actuales en config [15, 17]:")
for cur_l in [15, 17]:
    if cur_l in lag_dict:
        c = lag_dict[cur_l]
        print(f"    Lag {cur_l}: {c[1]}/{c[2]} ({c[3]:.2f}%) | Lift: {c[4]:.2f}x")

# 2. EVALUAR POR HORA DEL DÍA
print("\n--- 2. ANÁLISIS POR HORARIO DE SORTEO ---")
hora_groups = collections.defaultdict(list)
for i in range(len(nums)):
    hora_groups[horas[i]].append(nums[i])

print(f"{'HORA':<12} | {'TOTAL':<6} | {'REPETICIÓN LAG 1':<18} | {'ANIMALES ÚNICOS'}")
for h, h_nums in sorted(hora_groups.items()):
    rep_lag1 = sum(1 for j in range(1, len(h_nums)) if h_nums[j] == h_nums[j-1])
    rep_pct = rep_lag1 / len(h_nums) * 100 if len(h_nums) > 0 else 0
    n_uniq = len(set(h_nums))
    print(f"{h:<12} | {len(h_nums):<6} | {rep_lag1:>4} ({rep_pct:>5.1f}%)       | {n_uniq}/38")

# 3. CLUSTERING INTRADÍA
print("\n--- 3. CLUSTERING INTRADÍA (Repeticiones en el mismo día) ---")
cur_date = None
day_draws = []
dups_per_day = collections.defaultdict(int)
for i in range(N):
    d = fechas[i]
    if d != cur_date:
        cur_date = d
        day_draws = []
    if nums[i] in day_draws:
        dups_per_day[d] += 1
    day_draws.append(nums[i])

total_days = len(set(fechas))
total_dups = sum(dups_per_day.values())
avg_dups = total_dups / total_days if total_days > 0 else 0
print(f"  Total días analizados: {total_days}")
print(f"  Total duplicados intradía: {total_dups} (Promedio: {avg_dups:.2f} por día)")
print(f"  Días con 0 duplicados: {sum(1 for cnt in dups_per_day.values() if cnt == 0)}")
print(f"  Días con >= 3 duplicados: {sum(1 for cnt in dups_per_day.values() if cnt >= 3)}")

# 4. PARES DE MARKOV MÁS POTENTES
print("\n--- 4. TOP 8 PARES DE MARKOV (Transición Directa) ---")
pair_counts = collections.defaultdict(int)
for i in range(1, N):
    pair_counts[(nums[i-1], nums[i])] += 1

top_pairs = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)[:8]
for (n1, n2), cnt in top_pairs:
    p_trans = cnt / nums.count(n1) * 100
    lift_trans = p_trans / (100.0 / 38.0)
    print(f"  #{n1:>2} -> #{n2:>2}: {cnt:>3} veces ({p_trans:>5.2f}% condicional) | Lift: {lift_trans:.2f}x")

# 5. RENDIMIENTO POR GATILLO DE RACHA (0, 1, 2, 3, 4, 5, 6+)
print("\n--- 5. RENDIMIENTO SEGÚN POSICIÓN DE RACHA (Gatillos Sniper) ---")
best_lags = [lag_stats[0][0], lag_stats[1][0], lag_stats[2][0]]
print(f"  Probando con los 3 mejores lags empíricos: {best_lags}")

for target_streak in [0, 1, 2, 3, 4, 5]:
    streak = 0
    ops = 0
    wins = 0
    inv = 0.0
    cob = 0.0
    rec_w = 6
    for i in range(max(best_lags) + rec_w, N):
        actual = nums[i]
        rec_set = set(nums[i-rec_w:i])
        cands = list({nums[i-l] for l in best_lags} - rec_set)
        if streak == target_streak and cands:
            ops += 1
            cost = len(cands) * 1.0
            inv += cost
            hit = actual in cands
            if hit:
                wins += 1
                cob += payout * 1.0
        if cands:
            streak = 0 if actual in cands else streak + 1
    
    wr = wins / ops * 100 if ops > 0 else 0
    pnl = cob - inv
    roi = pnl / inv * 100 if inv > 0 else 0
    print(f"  Disparar en Racha {target_streak}: {ops:>4} ops | {wins:>3} wins | WR: {wr:>5.2f}% | PnL: {pnl:>+8.2f} | ROI: {roi:>+6.2f}%")
