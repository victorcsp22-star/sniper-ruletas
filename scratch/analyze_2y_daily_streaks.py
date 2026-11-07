import os
import sys
import json
import math
from collections import defaultdict
import numpy as np
import pandas as pd
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = r"C:\Users\victo\nuevas_ruletas"
sys.path.append(ROOT_DIR)

from config import RULETAS_CONFIG

print("=" * 90)
print("ANÁLISIS ESTOCÁSTICO DE DÍAS Y SEGUIDILLAS (2 AÑOS COMPLETOS / 7 RULETAS)")
print("=" * 90)

all_series = {}
for r_name, cfg in RULETAS_CONFIG.items():
    if not cfg.get("active", False) or "rec_w" not in cfg:
        continue
    df = pd.read_csv(cfg["file"], dtype={"numero": str})
    df["numero"] = df["numero"].astype(str).str.strip()
    df["animal"] = df["animal"].astype(str).str.strip()
    df["fecha"] = df["fecha"].astype(str).str.strip()
    df["hora"] = df["hora"].astype(str).str.strip()
    df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
    df = df.dropna(subset=["sort_dt"]).sort_values("sort_dt").reset_index(drop=True)
    all_series[r_name] = df

# 1. Generar eventos cronológicos sin look-ahead (Fichas fijas de $1.00 USD)
events = []

for r_name, df in all_series.items():
    cfg = RULETAS_CONFIG[r_name]
    lags = cfg["lags"]
    rec_w = cfg["rec_w"]
    target_streaks = cfg.get("target_streaks", [1])
    use_anti_cluster = cfg.get("anti_clustering", False)
    blacklist = set(cfg.get("blacklist", []))
    markov_snipers = cfg.get("markov_snipers", {})
    payout = cfg["payout"]

    nums = df["numero"].tolist()
    dts = df["sort_dt"].tolist()
    fechas = df["fecha"].tolist()
    horas = df["hora"].tolist()
    animals = df["animal"].tolist()

    streak = 0
    trigger_misses = 0
    cur_d = None
    seen_today = set()
    prev_was_repeat = False

    min_k = max(max(lags), rec_w) + 1

    for i in range(min_k, len(nums)):
        actual = nums[i]
        d = fechas[i]
        h = horas[i]
        prev_num = nums[i - 1]

        if d != cur_d:
            cur_d = d
            seen_today = set()
            prev_was_repeat = False

        rec_set = set(nums[i - rec_w : i])
        raw_cands = [nums[i - l] for l in lags if i - l >= 0]
        cands_lag = sorted(list((set(raw_cands) - rec_set) - blacklist))

        skip_anti_cluster = bool(use_anti_cluster and prev_was_repeat)

        # Canal A: Disparo de Canasta por Lags Armónicos
        if cands_lag and not skip_anti_cluster:
            hit_lag = (actual in cands_lag)
            if streak in target_streaks:
                events.append({
                    "dt": dts[i],
                    "fecha": d,
                    "hora": h,
                    "ruleta": r_name,
                    "channel": "Canal_A_Lag",
                    "cands": cands_lag,
                    "actual": actual,
                    "actual_anim": animals[i],
                    "hit": hit_lag,
                    "payout": payout,
                    "idx": i
                })
            streak = 0 if hit_lag else streak + 1
        elif cands_lag and skip_anti_cluster:
            hit_lag = (actual in cands_lag)
            streak = 0 if hit_lag else streak + 1

        # Canal B: Disparo Markov Sniper Mono-Animal
        markov_target = markov_snipers.get(prev_num)
        if markov_target and markov_target not in rec_set and markov_target not in blacklist:
            m_hit = (actual == markov_target)
            events.append({
                "dt": dts[i],
                "fecha": d,
                "hora": h,
                "ruleta": r_name,
                "channel": "Canal_B_Markov",
                "cands": [markov_target],
                "actual": actual,
                "actual_anim": animals[i],
                "hit": m_hit,
                "payout": payout,
                "idx": i
            })

        is_repeat = (actual in seen_today)
        seen_today.add(actual)
        prev_was_repeat = is_repeat

events.sort(key=lambda x: x["dt"])
print(f"Total de operaciones ejecutadas en 2 años: {len(events)}")

# Simular con $1.00 USD fijo por animalito
STAKE_UNIT = 1.00
daily_data = defaultdict(lambda: {"bet": 0.0, "cob": 0.0, "ops": 0, "wins": 0})

for ev in events:
    d = ev["fecha"]
    cands_count = len(ev["cands"])
    bet = cands_count * STAKE_UNIT
    cob = (STAKE_UNIT * ev["payout"]) if ev["hit"] else 0.0
    
    daily_data[d]["bet"] += bet
    daily_data[d]["cob"] += cob
    daily_data[d]["ops"] += 1
    if ev["hit"]:
        daily_data[d]["wins"] += 1

# Convertir a lista ordenada cronológicamente
all_dates = sorted(daily_data.keys())
daily_records = []
for d in all_dates:
    b = daily_data[d]["bet"]
    c = daily_data[d]["cob"]
    pnl = round(c - b, 2)
    state = "W" if pnl > 0 else ("L" if pnl < 0 else "N")
    daily_records.append({
        "fecha": d,
        "bet": b,
        "cob": c,
        "pnl": pnl,
        "ops": daily_data[d]["ops"],
        "wins": daily_data[d]["wins"],
        "state": state
    })

df_days = pd.DataFrame(daily_records)

# Totales
tot_days = len(df_days)
win_days = (df_days["state"] == "W").sum()
loss_days = (df_days["state"] == "L").sum()
neutral_days = (df_days["state"] == "N").sum()

win_rate_days = (win_days / tot_days) * 100

print(f"Total días operados en 2 años : {tot_days} días")
print(f"  • Días Ganadores (PnL > 0)  : {win_days} días ({win_rate_days:.2f}%)")
print(f"  • Días Perdedores (PnL < 0) : {loss_days} días ({(loss_days / tot_days)*100:.2f}%)")
print(f"  • Días Neutros (PnL == 0)   : {neutral_days} días ({(neutral_days / tot_days)*100:.2f}%)")

# 2. Análisis de Transiciones Markov tras un día de pérdida:
# L -> W (Ganar después de perder)
# L -> L (Perder después de perder)
# L -> N (Neutro después de perder)
transitions_from_L = {"W": 0, "L": 0, "N": 0}
states_seq = df_days["state"].tolist()

for i in range(len(states_seq) - 1):
    curr_s = states_seq[i]
    next_s = states_seq[i + 1]
    if curr_s == "L":
        transitions_from_L[next_s] += 1

total_after_L = sum(transitions_from_L.values())
pct_L_to_W = (transitions_from_L["W"] / total_after_L) * 100 if total_after_L > 0 else 0
pct_L_to_L = (transitions_from_L["L"] / total_after_L) * 100 if total_after_L > 0 else 0
pct_L_to_N = (transitions_from_L["N"] / total_after_L) * 100 if total_after_L > 0 else 0

print("\n" + "=" * 90)
print("COMPORTAMIENTO LUEGO DE UN DÍA DE PÉRDIDA:")
print("=" * 90)
print(f"Total de días que siguieron a un día de pérdida: {total_after_L}")
print(f"  • Día Positivo / Ganador luego de perder (L -> W)  : {transitions_from_L['W']} veces ({pct_L_to_W:.2f}%)  <-- Tasa de Rebote Inmediato")
print(f"  • Día Negativo / Seguido de pérdida (L -> L)      : {transitions_from_L['L']} veces ({pct_L_to_L:.2f}%)  <-- Persistencia de pérdida")
if transitions_from_L['N'] > 0:
    print(f"  • Día Neutro (PnL 0) luego de perder (L -> N)    : {transitions_from_L['N']} veces ({pct_L_to_N:.2f}%)")

# 3. Seguidillas de Días Ganadores y Días Perdedores
# Agrupar rachas consecutivas
win_streaks = defaultdict(int)
loss_streaks = defaultdict(int)

cur_state = None
cur_len = 0

for s in states_seq:
    if s == cur_state:
        cur_len += 1
    else:
        if cur_state == "W":
            win_streaks[cur_len] += 1
        elif cur_state == "L":
            loss_streaks[cur_len] += 1
        cur_state = s
        cur_len = 1

# Última racha
if cur_state == "W":
    win_streaks[cur_len] += 1
elif cur_state == "L":
    loss_streaks[cur_len] += 1

print("\n" + "=" * 90)
print("SEGUIDILLAS DE DÍAS GANADORES CONSECUTIVOS (DISTRIBUCIÓN FRECUENCIAL):")
print("=" * 90)
max_win_len = max(win_streaks.keys()) if win_streaks else 0
total_win_clusters = sum(win_streaks.values())

for length in sorted(win_streaks.keys()):
    count = win_streaks[length]
    pct = (count / total_win_clusters) * 100
    total_days_in_streak = length * count
    bar = "█" * int(pct / 2)
    print(f"  Seguidilla de {length:2d} día(s) ganado(s) seguido(s) : {count:3d} veces ({pct:5.1f}%) | Aporta {total_days_in_streak:3d} días ganadores {bar}")

print(f"\nRacha Ganadora Máxima Histórica: {max_win_len} DÍAS GANADORES CONSECUTIVOS")

print("\n" + "=" * 90)
print("SEGUIDILLAS DE DÍAS PERDEDORES CONSECUTIVOS (DISTRIBUCIÓN FRECUENCIAL):")
print("=" * 90)
max_loss_len = max(loss_streaks.keys()) if loss_streaks else 0
total_loss_clusters = sum(loss_streaks.values())

for length in sorted(loss_streaks.keys()):
    count = loss_streaks[length]
    pct = (count / total_loss_clusters) * 100
    total_days_in_streak = length * count
    bar = "█" * int(pct / 2)
    print(f"  Seguidilla de {length:2d} día(s) perdido(s) seguido(s) : {count:3d} veces ({pct:5.1f}%) | Aporta {total_days_in_streak:3d} días perdedores {bar}")

print(f"\nRacha Perdedora Máxima Histórica: {max_loss_len} DÍAS PERDEDORES CONSECUTIVOS")
print("=" * 90)
