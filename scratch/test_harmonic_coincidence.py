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
N = len(nums)

# Test 1: Sorteos donde existe coincidencia armónica (Lag 20 coincide con Lag 18 o Lag 14 o Lag 55)
trades_coincidence = []
trades_base = []
streak = 0
cur_date = None
seen_today = set()
prev_was_repeat = False

for i in range(56, N):
    actual = nums[i]
    d = df.iloc[i]["fecha"]

    if d != cur_date:
        cur_date = d
        seen_today = set()
        prev_was_repeat = False

    rec6 = set(nums[i-6:i])
    l20 = nums[i-20]
    l18 = nums[i-18]
    l14 = nums[i-14]
    l55 = nums[i-55]

    cands_std = sorted(list(set([l20, l18, l14]) - rec6))
    skip_ac = prev_was_repeat

    if cands_std and not skip_ac:
        hit = (actual in cands_std)
        if streak == 1:
            # Check if there is harmonic coincidence (any two lags coincide)
            has_resonance = (l20 == l18 or l20 == l14 or l18 == l14 or l20 == l55 or l18 == l55)
            trades_base.append({"hit": hit, "cost": len(cands_std), "has_resonance": has_resonance})
        streak = 0 if hit else streak + 1
    elif cands_std and skip_ac:
        hit = (actual in cands_std)
        streak = 0 if hit else streak + 1

    is_rep = (actual in seen_today)
    seen_today.add(actual)
    prev_was_repeat = is_rep

res_sub = [t for t in trades_base if t["has_resonance"]]
n_res = len(res_sub)
hits_res = sum(1 for t in res_sub if t["hit"])
inv_res = sum(t["cost"] for t in res_sub)
col_res = sum(30.0 for t in res_sub if t["hit"])
roi_res = (col_res - inv_res) / inv_res * 100.0 if inv_res > 0 else 0

print(f"Sub-universo con Coincidencia Armónica (Resonancia entre Lags):")
print(f"  Disparos: {n_res} | Aciertos: {hits_res} ({hits_res/n_res*100:.2f}%) | ROI: {roi_res:+.2f}%")
