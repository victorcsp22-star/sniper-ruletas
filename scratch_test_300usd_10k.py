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
                    "ruleta": r_name,
                    "cost_units": cost_units,
                    "hit": hit,
                    "payout": payout,
                    "f_unit": f_unit,
                    "is_60x": (payout == 60.0)
                })
            streak = 0 if hit else streak + 1

all_events.sort(key=lambda x: x["dt"])

# 1. Full continuous run starting from $300
b = 300.0
reach_10k_date = None
start_d = all_events[0]["dt"]

for ev in all_events:
    stake_u = max(0.10, b * ev["f_unit"])
    tot_s = stake_u * ev["cost_units"]
    if ev["hit"]:
        pnl = stake_u * ev["payout"] - tot_s
    else:
        pnl = -tot_s
    b = max(1.0, b + pnl)
    if b >= 10000.0 and reach_10k_date is None:
        reach_10k_date = ev["dt"]

days_300 = (reach_10k_date - start_d).total_seconds() / 86400.0 if reach_10k_date else None
print(f"--- Carrera Continua Completa desde $300 ---")
print(f"Alcanzó $10,000 el: {reach_10k_date} ({days_300:.1f} días / {days_300/30.0:.1f} meses)")

# 2. Ventanas de 60 días para $300 bajo diferentes multiplicadores de Kelly
start_dts = [all_events[0]["dt"] + timedelta(days=i*15) for i in range(45)]

print(f"\n--- Ventanas de 60 Días Iniciando con $300 USD ---")
print(f"{'Multiplicador':<16} | {'Éxito $10k':<12} | {'Ruina (<$10)':<12} | {'Mediana Final':<14} | {'Máximo Final':<12} | {'MDD Promedio'}")
print("-" * 85)

for k_mult in [1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]:
    caps = 0
    ruins = 0
    finals = []
    mdds = []
    total = 0
    
    for s_dt in start_dts:
        match_idx = None
        for i, ev in enumerate(all_events):
            if ev["dt"] >= s_dt:
                match_idx = i
                break
        if match_idx is None or match_idx >= len(all_events) - 50:
            continue
            
        total += 1
        end_dt = s_dt + timedelta(days=60)
        bankroll = 300.0
        peak = 300.0
        min_b = 300.0
        hit = False
        
        for idx in range(match_idx, len(all_events)):
            ev = all_events[idx]
            if ev["dt"] > end_dt:
                break
            stake_u = max(0.10, bankroll * ev["f_unit"] * k_mult)
            tot_s = min(bankroll * 0.40, stake_u * ev["cost_units"])
            u_act = tot_s / ev["cost_units"]
            
            if ev["hit"]:
                pnl = u_act * ev["payout"] - tot_s
            else:
                pnl = -tot_s
                
            bankroll += pnl
            if bankroll < min_b:
                min_b = bankroll
            if bankroll > peak:
                peak = bankroll
            if bankroll >= 10000.0:
                hit = True
                bankroll = 10000.0
                break
            if bankroll <= 10.0:
                break
                
        if hit:
            caps += 1
        if bankroll <= 10.0:
            ruins += 1
        finals.append(bankroll)
        mdds.append((peak - min_b) / peak if peak > 0 else 1.0)
        
    print(f"Kelly {k_mult:4.2f}x    | {caps}/{total} ({caps/total*100:4.1f}%) | {ruins}/{total} ({ruins/total*100:4.1f}%) | ${np.median(finals):10.2f}   | ${np.max(finals):10.2f} | {np.mean(mdds)*100:5.1f}%")

# 3. Protocolo Asimétrico 3 Fases con $300
print(f"\n--- Protocolo Asimétrico por Hitos (3 Fases) Iniciando con $300 USD en 60 Días ---")
def sim_asym_ratchet_300(events, start_idx, days=60):
    start_dt = events[start_idx]["dt"]
    end_dt = start_dt + timedelta(days=days)
    bankroll = 300.0
    peak = 300.0
    min_b = 300.0
    hit = False
    
    for idx in range(start_idx, len(events)):
        ev = events[idx]
        if ev["dt"] > end_dt:
            break
            
        if bankroll < 1200.0:
            k_mult = 1.8 if ev["is_60x"] else 1.2
            floor = 150.0
        elif bankroll < 4000.0:
            k_mult = 1.4 if ev["is_60x"] else 1.0
            floor = 900.0
        else:
            k_mult = 1.0
            floor = 3000.0
            
        cushion = max(0.05, (bankroll - floor) / bankroll)
        damping = min(1.0, cushion ** 0.8)
        
        stake_u = max(0.10, bankroll * ev["f_unit"] * k_mult * damping)
        tot_s = min(bankroll * 0.35, stake_u * ev["cost_units"])
        u_act = tot_s / ev["cost_units"]
        
        if ev["hit"]:
            pnl = u_act * ev["payout"] - tot_s
        else:
            pnl = -tot_s
            
        bankroll += pnl
        if bankroll < min_b:
            min_b = bankroll
        if bankroll > peak:
            peak = bankroll
        if bankroll >= 10000.0:
            hit = True
            bankroll = 10000.0
            break
        if bankroll <= 10.0:
            break
            
    return {"final": bankroll, "hit": hit, "mdd": (peak - min_b) / peak if peak > 0 else 1.0}

caps_r = 0
ruins_r = 0
finals_r = []
mdds_r = []
for s_dt in start_dts:
    match_idx = None
    for i, ev in enumerate(all_events):
        if ev["dt"] >= s_dt:
            match_idx = i
            break
    if match_idx is None or match_idx >= len(all_events) - 50:
        continue
    res = sim_asym_ratchet_300(all_events, match_idx, 60)
    if res["hit"]:
        caps_r += 1
    if res["final"] <= 10.0:
        ruins_r += 1
    finals_r.append(res["final"])
    mdds_r.append(res["mdd"])

total_r = len(finals_r)
print(f"Hitos Asimétricos | {caps_r}/{total_r} ({caps_r/total_r*100:4.1f}%) | {ruins_r}/{total_r} ({ruins_r/total_r*100:4.1f}%) | ${np.median(finals_r):10.2f}   | ${np.max(finals_r):10.2f} | {np.mean(mdds_r)*100:5.1f}%")

# 4. Sensibilidad temporal desde $300 (60, 75, 90, 105, 120 días)
print(f"\n--- Sensibilidad por Plazo Temporal Iniciando con $300 USD (Kelly 1.25x) ---")
for horizon in [60, 75, 90, 105, 120, 150]:
    c_h = 0
    r_h = 0
    f_h = []
    tot_h = 0
    for s_dt in start_dts:
        match_idx = None
        for i, ev in enumerate(all_events):
            if ev["dt"] >= s_dt:
                match_idx = i
                break
        if match_idx is None or match_idx >= len(all_events) - 50:
            continue
        tot_h += 1
        end_dt = s_dt + timedelta(days=horizon)
        b = 300.0
        hit = False
        for idx in range(match_idx, len(all_events)):
            ev = all_events[idx]
            if ev["dt"] > end_dt:
                break
            stake_u = max(0.10, b * ev["f_unit"] * 1.25)
            tot_s = min(b * 0.35, stake_u * ev["cost_units"])
            u_act = tot_s / ev["cost_units"]
            if ev["hit"]:
                pnl = u_act * ev["payout"] - tot_s
            else:
                pnl = -tot_s
            b = max(1.0, b + pnl)
            if b >= 10000.0:
                hit = True
                b = 10000.0
                break
            if b <= 10.0:
                break
        if hit:
            c_h += 1
        if b <= 10.0:
            r_h += 1
        f_h.append(b)
    print(f"Plazo {horizon:3d} días ({horizon/30:3.1f}m) | Éxito $10k: {c_h}/{tot_h} ({c_h/tot_h*100:4.1f}%) | Ruina: {r_h}/{tot_h} ({r_h/tot_h*100:4.1f}%) | Mediana: ${np.median(f_h):8.2f} | Máx: ${np.max(f_h):8.2f}")
