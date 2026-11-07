import os
import sys
import pandas as pd
import numpy as np
from datetime import timedelta

VZ_DIR = r"C:\Users\victo\.gemini\antigravity\scratch\lotto_activo_bot"
NEW_DIR = r"C:\Users\victo\nuevas_ruletas"

CONFIG_7 = {
    "Lotto Activo": {"file": os.path.join(VZ_DIR, "lotto_activo_2anios.csv"), "lags": [20, 18, 14], "payout": 30.0, "f_unit": 0.00900, "target_streaks": [1]},
    "La Granjita": {"file": os.path.join(VZ_DIR, "la_granjita_2anios.csv"), "lags": [15, 17], "payout": 30.0, "f_unit": 0.00484, "target_streaks": [1]},
    "Ruleta Royal": {"file": os.path.join(VZ_DIR, "ruleta_royal_2anios.csv"), "lags": [16, 19, 31], "payout": 30.0, "f_unit": 0.00826, "target_streaks": [1]},
    "Guacharo Activo": {"file": os.path.join(VZ_DIR, "guacharo_activo_2anios.csv"), "lags": [31, 41, 25, 42, 35], "payout": 60.0, "f_unit": 0.00680, "target_streaks": [1]},
    "Gatazo": {"file": os.path.join(NEW_DIR, "gatazo.csv"), "lags": [35, 22, 20], "payout": 60.0, "f_unit": 0.00900, "target_streaks": [1, 2]},
    "Mega Animal 40": {"file": os.path.join(NEW_DIR, "mega_animal_40.csv"), "lags": [18, 21, 37], "payout": 30.0, "f_unit": 0.00800, "target_streaks": [1]},
    "Monje Millonario": {"file": os.path.join(NEW_DIR, "monje_millonario.csv"), "lags": [24, 35, 37], "payout": 60.0, "f_unit": 0.00700, "target_streaks": [1]}
}

all_events = []
for r_name, cfg in CONFIG_7.items():
    if not os.path.exists(cfg["file"]):
        continue
    df = pd.read_csv(cfg["file"], dtype={"numero": str})
    df["numero"] = df["numero"].astype(str).str.strip()
    df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
    df = df.sort_values(by="sort_dt").reset_index(drop=True)
    lags = cfg["lags"]
    payout = cfg["payout"]
    f_unit = cfg["f_unit"]
    target_streaks = cfg["target_streaks"]
    nums = df["numero"].tolist()
    min_idx = max(lags) + 6
    streak = 0
    for i in range(min_idx, len(nums)):
        actual = nums[i]
        rec6 = set(nums[i-6:i])
        cands = list({nums[i-l] for l in lags} - rec6)
        if cands:
            cost_units = len(cands)
            hit = (actual in cands)
            if streak in target_streaks:
                all_events.append({
                    "dt": df.iloc[i]["sort_dt"],
                    "cost_units": cost_units,
                    "hit": hit,
                    "payout": payout,
                    "f_unit": f_unit
                })
            streak = 0 if hit else streak + 1

all_events.sort(key=lambda x: x["dt"])

# Simular con Full Kelly Puro comenzando desde $200 para ver en qué momento de la historia alcanzó $10,000
def full_history_sim():
    b = 200.0
    peak = 200.0
    history = []
    reach_10k_date = None
    
    for ev in all_events:
        stake_u = max(0.10, b * ev["f_unit"])
        tot_stake = stake_u * ev["cost_units"]
        if ev["hit"]:
            cob = stake_u * ev["payout"]
            pnl = cob - tot_stake
        else:
            cob = 0.0
            pnl = -tot_stake
        b = max(1.0, b + pnl)
        if b > peak:
            peak = b
        history.append((ev["dt"], b))
        if b >= 10000.0 and reach_10k_date is None:
            reach_10k_date = ev["dt"]
            
    return history, reach_10k_date

hist, d_10k = full_history_sim()
start_d = hist[0][0]
print(f"Inicio: {start_d} con $200.00")
if d_10k:
    days_taken = (d_10k - start_d).total_seconds() / 86400.0
    print(f"Alcanzó $10,000 por primera vez el: {d_10k} ({days_taken:.1f} días / {days_taken/30.0:.1f} meses)")
else:
    print("No alcanzó $10,000 en la simulación")

# Evaluar ventanas de diferentes duraciones: 60, 90, 120, 180 días
start_dts = [all_events[0]["dt"] + timedelta(days=i*15) for i in range(40)]

for horizon_days in [60, 90, 120, 150, 180]:
    caps = 0
    total = 0
    finals = []
    ruins = 0
    for s_dt in start_dts:
        match_idx = None
        for i, ev in enumerate(all_events):
            if ev["dt"] >= s_dt:
                match_idx = i
                break
        if match_idx is None or match_idx >= len(all_events) - 50:
            continue
            
        end_dt = s_dt + timedelta(days=horizon_days)
        b = 200.0
        hit = False
        for idx in range(match_idx, len(all_events)):
            ev = all_events[idx]
            if ev["dt"] > end_dt:
                break
            stake_u = max(0.10, b * ev["f_unit"] * 1.0)
            tot_s = stake_u * ev["cost_units"]
            if ev["hit"]:
                pnl = stake_u * ev["payout"] - tot_s
            else:
                pnl = -tot_s
            b = max(1.0, b + pnl)
            if b >= 10000.0:
                hit = True
                b = 10000.0
                break
            if b <= 10.0:
                break
        total += 1
        if hit:
            caps += 1
        if b <= 10.0:
            ruins += 1
        finals.append(b)
    print(f"Horizonte {horizon_days:3d} días ({horizon_days/30:3.1f} meses): Éxito $10k = {caps}/{total} ({caps/total*100:4.1f}%) | Ruina = {ruins}/{total} ({ruins/total*100:4.1f}%) | Mediana = ${np.median(finals):8.2f} | Máx = ${np.max(finals):8.2f}")
