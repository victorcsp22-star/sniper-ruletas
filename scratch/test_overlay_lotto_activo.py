import os
import sys
import pandas as pd
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

FILE_PATH = r"C:\Users\victo\nuevas_ruletas\data_vz\lotto_activo_2anios.csv"
df = pd.read_csv(FILE_PATH, dtype={"numero": str})
df["numero"] = df["numero"].astype(str).str.strip()
df["fecha"] = df["fecha"].astype(str).str.strip()
df["hora"] = df["hora"].astype(str).str.strip()
df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
df = df.dropna(subset=["sort_dt"]).sort_values("sort_dt").reset_index(drop=True)

nums = df["numero"].tolist()
hours = df["hora"].tolist()
N = len(nums)

# Markov boost pairs:
markov_boost = {
    "13": "6",
    "6": "1",
    "5": "4",
    "16": "28"
}

# Standard Maximized Strategy for Lotto Activo:
# lags = [20, 18, 14], rec_w = 6, anti_clustering = True
lags = [20, 18, 14]
rec_w = 6

cur_date = None
seen_today = set()
prev_was_repeat = False

trades_standard = []
trades_with_markov = []

streak = 0
for i in range(max(lags) + rec_w + 1, N):
    actual = nums[i]
    d = df.iloc[i]["fecha"]
    h = df.iloc[i]["hora"]
    prev_num = nums[i-1]

    if d != cur_date:
        cur_date = d
        seen_today = set()
        prev_was_repeat = False

    rec_set = set(nums[i - rec_w : i])
    raw_lags = [nums[i - l] for l in lags]
    cands_std = sorted(list(set(raw_lags) - rec_set))

    # Anti-cluster gate
    skip_ac = prev_was_repeat

    if cands_std and not skip_ac:
        hit = (actual in cands_std)
        if streak == 1:
            trades_standard.append({
                "hit": hit,
                "cost": len(cands_std),
                "payout": 30.0 if hit else 0.0
            })
        streak = 0 if hit else streak + 1
    elif cands_std and skip_ac:
        hit = (actual in cands_std)
        streak = 0 if hit else streak + 1

    is_rep = (actual in seen_today)
    seen_today.add(actual)
    prev_was_repeat = is_rep

# Evaluation of standard
n_std = len(trades_standard)
hits_std = sum(1 for t in trades_standard if t["hit"])
inv_std = sum(t["cost"] for t in trades_standard)
col_std = sum(t["payout"] for t in trades_standard)
roi_std = (col_std - inv_std) / inv_std * 100.0

print(f"Lotto Activo - Estrategia Actual (2 Años):")
print(f"  Disparos: {n_std} | Aciertos: {hits_std} ({hits_std/n_std*100:.2f}%) | ROI: {roi_std:+.2f}%")

# Now let's test if incorporating Lag 55 (el ciclo semanal exacto a la misma hora)
lags_with_55 = [20, 18, 14, 55]
streak_55 = 0
cur_date = None
seen_today = set()
prev_was_repeat = False
trades_55 = []

for i in range(56 + rec_w + 1, N):
    actual = nums[i]
    d = df.iloc[i]["fecha"]
    h = df.iloc[i]["hora"]

    if d != cur_date:
        cur_date = d
        seen_today = set()
        prev_was_repeat = False

    rec_set = set(nums[i - rec_w : i])
    raw_lags = [nums[i - l] for l in lags_with_55]
    cands_55 = sorted(list(set(raw_lags) - rec_set))

    skip_ac = prev_was_repeat

    if cands_55 and not skip_ac:
        hit = (actual in cands_55)
        if streak_55 == 1:
            trades_55.append({
                "hit": hit,
                "cost": len(cands_55),
                "payout": 30.0 if hit else 0.0
            })
        streak_55 = 0 if hit else streak_55 + 1
    elif cands_55 and skip_ac:
        hit = (actual in cands_55)
        streak_55 = 0 if hit else streak_55 + 1

    is_rep = (actual in seen_today)
    seen_today.add(actual)
    prev_was_repeat = is_rep

n_55 = len(trades_55)
hits_55 = sum(1 for t in trades_55 if t["hit"])
inv_55 = sum(t["cost"] for t in trades_55)
col_55 = sum(t["payout"] for t in trades_55)
roi_55 = (col_55 - inv_55) / inv_55 * 100.0

print(f"\nLotto Activo - Experimento con Lag 55 (Ciclo Semanal Exacto de Horario):")
print(f"  Disparos: {n_55} | Aciertos: {hits_55} ({hits_55/n_55*100:.2f}%) | ROI: {roi_55:+.2f}%")
