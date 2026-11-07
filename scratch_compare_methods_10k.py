import os
import sys
import pandas as pd
import numpy as np
from datetime import timedelta

VZ_DIR = r"C:\Users\victo\.gemini\antigravity\scratch\lotto_activo_bot"
NEW_DIR = r"C:\Users\victo\nuevas_ruletas"

CONFIG_7 = {
    "Lotto Activo": {
        "file": os.path.join(VZ_DIR, "lotto_activo_2anios.csv"),
        "lags": [20, 18, 14],
        "payout": 30.0,
        "f_unit": 0.00900,
        "target_streaks": [1],
    },
    "La Granjita": {
        "file": os.path.join(VZ_DIR, "la_granjita_2anios.csv"),
        "lags": [15, 17],
        "payout": 30.0,
        "f_unit": 0.00484,
        "target_streaks": [1],
    },
    "Ruleta Royal": {
        "file": os.path.join(VZ_DIR, "ruleta_royal_2anios.csv"),
        "lags": [16, 19, 31],
        "payout": 30.0,
        "f_unit": 0.00826,
        "target_streaks": [1],
    },
    "Guacharo Activo": {
        "file": os.path.join(VZ_DIR, "guacharo_activo_2anios.csv"),
        "lags": [31, 41, 25, 42, 35],
        "payout": 60.0,
        "f_unit": 0.00680,
        "target_streaks": [1],
    },
    "Gatazo": {
        "file": os.path.join(NEW_DIR, "gatazo.csv"),
        "lags": [35, 22, 20],
        "payout": 60.0,
        "f_unit": 0.00900,
        "target_streaks": [1, 2],
    },
    "Mega Animal 40": {
        "file": os.path.join(NEW_DIR, "mega_animal_40.csv"),
        "lags": [18, 21, 37],
        "payout": 30.0,
        "f_unit": 0.00800,
        "target_streaks": [1],
    },
    "Monje Millonario": {
        "file": os.path.join(NEW_DIR, "monje_millonario.csv"),
        "lags": [24, 35, 37],
        "payout": 60.0,
        "f_unit": 0.00700,
        "target_streaks": [1],
    }
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
            if hit:
                streak = 0
            else:
                streak += 1

all_events.sort(key=lambda x: x["dt"])

# METODO 1: Escalamiento Dinámico por Hitos (Milestone Ratchet Compounder)
# Fase 1: $200 - $1,000 (Multiplicador agresivo 1.8x para salir de la zona micro)
# Fase 2: $1,000 - $3,000 (Multiplicador 1.4x, piso protegido en $600)
# Fase 3: $3,000 - $10,000 (Multiplicador 1.2x, piso protegido en $2,000)
def sim_milestone_ratchet(events, start_idx, days=60, max_cap=10000.0, min_bet=0.10):
    start_dt = events[start_idx]["dt"]
    end_dt = start_dt + timedelta(days=days)
    bankroll = 200.0
    peak = 200.0
    min_b = 200.0
    hit_cap = False
    cap_dt = None

    for idx in range(start_idx, len(events)):
        ev = events[idx]
        if ev["dt"] > end_dt:
            break

        # Determinar fase y multiplicador
        if bankroll < 1000.0:
            k_mult = 2.0
            floor = 100.0
        elif bankroll < 3000.0:
            k_mult = 1.5
            floor = 700.0
        else:
            k_mult = 1.2
            floor = 2200.0

        # Amortiguador de colchón respecto al piso de fase
        cushion = max(0.05, (bankroll - floor) / bankroll)
        damping = min(1.0, cushion ** 1.0)

        stake_unit = max(min_bet, bankroll * ev["f_unit"] * k_mult * damping)
        total_stake = min(bankroll * 0.35, stake_unit * ev["cost_units"])
        unit_actual = total_stake / ev["cost_units"]

        if ev["hit"]:
            cob = unit_actual * ev["payout"]
            pnl = cob - total_stake
        else:
            pnl = -total_stake

        bankroll += pnl
        if bankroll < min_b:
            min_b = bankroll
        if bankroll > peak:
            peak = bankroll

        if bankroll >= max_cap:
            hit_cap = True
            cap_dt = ev["dt"]
            bankroll = max_cap
            break
        if bankroll <= 10.0:
            break

    return {
        "start_dt": start_dt,
        "end_dt": end_dt,
        "final_bankroll": bankroll,
        "min_bankroll": min_b,
        "hit_cap": hit_cap,
        "days_to_cap": (cap_dt - start_dt).total_seconds() / 86400.0 if hit_cap else None,
        "mdd": (peak - min_b) / peak if peak > 0 else 1.0
    }

# METODO 2: Concentración Asimétrica 60x (Priorizar o ponderar más ruletas 60x donde 1 acierto = +57u)
def sim_asymmetric_60x(events, start_idx, days=60, max_cap=10000.0, min_bet=0.10):
    start_dt = events[start_idx]["dt"]
    end_dt = start_dt + timedelta(days=days)
    bankroll = 200.0
    peak = 200.0
    min_b = 200.0
    hit_cap = False
    cap_dt = None

    for idx in range(start_idx, len(events)):
        ev = events[idx]
        if ev["dt"] > end_dt:
            break

        # Las ruletas de payout 60x tienen mayor esperanza matemática asimétrica
        # Aumentamos ponderación en 60x (Gatazo, Guácharo, Monje)
        mult_60x = 2.2 if ev["is_60x"] else 1.2

        stake_unit = max(min_bet, bankroll * ev["f_unit"] * mult_60x)
        total_stake = min(bankroll * 0.35, stake_unit * ev["cost_units"])
        unit_actual = total_stake / ev["cost_units"]

        if ev["hit"]:
            cob = unit_actual * ev["payout"]
            pnl = cob - total_stake
        else:
            pnl = -total_stake

        bankroll += pnl
        if bankroll < min_b:
            min_b = bankroll
        if bankroll > peak:
            peak = bankroll

        if bankroll >= max_cap:
            hit_cap = True
            cap_dt = ev["dt"]
            bankroll = max_cap
            break
        if bankroll <= 10.0:
            break

    return {
        "start_dt": start_dt,
        "end_dt": end_dt,
        "final_bankroll": bankroll,
        "min_bankroll": min_b,
        "hit_cap": hit_cap,
        "days_to_cap": (cap_dt - start_dt).total_seconds() / 86400.0 if hit_cap else None,
        "mdd": (peak - min_b) / peak if peak > 0 else 1.0
    }

# METODO 3: Reinicio Semanal con Interés Compuesto Agresivo (Weekly Reset & Compound)
def sim_weekly_reset_compound(events, start_idx, days=60, base_unit=1.0, max_cap=10000.0):
    start_dt = events[start_idx]["dt"]
    end_dt = start_dt + timedelta(days=days)
    bankroll = 200.0
    peak = 200.0
    min_b = 200.0
    hit_cap = False
    cap_dt = None

    current_week = None
    week_start_b = 200.0
    stake_unit = 0.50

    for idx in range(start_idx, len(events)):
        ev = events[idx]
        if ev["dt"] > end_dt:
            break

        week_id = ev["dt"].isocalendar()[:2]
        if week_id != current_week:
            current_week = week_id
            week_start_b = bankroll
            # Recalcular apuesta unitaria fija para la semana: 0.8% del capital al inicio de semana
            stake_unit = max(0.10, week_start_b * 0.008)

        total_stake = min(bankroll * 0.30, stake_unit * ev["cost_units"])
        unit_actual = total_stake / ev["cost_units"]

        if ev["hit"]:
            cob = unit_actual * ev["payout"]
            pnl = cob - total_stake
        else:
            pnl = -total_stake

        bankroll += pnl
        if bankroll < min_b:
            min_b = bankroll
        if bankroll > peak:
            peak = bankroll

        if bankroll >= max_cap:
            hit_cap = True
            cap_dt = ev["dt"]
            bankroll = max_cap
            break
        if bankroll <= 10.0:
            break

    return {
        "start_dt": start_dt,
        "end_dt": end_dt,
        "final_bankroll": bankroll,
        "min_bankroll": min_b,
        "hit_cap": hit_cap,
        "days_to_cap": (cap_dt - start_dt).total_seconds() / 86400.0 if hit_cap else None,
        "mdd": (peak - min_b) / peak if peak > 0 else 1.0
    }

start_dts = [all_events[0]["dt"] + timedelta(days=i*15) for i in range(45)]

methods = {
    "Milestone Ratchet": sim_milestone_ratchet,
    "Asymmetric 60x": sim_asymmetric_60x,
    "Weekly Reset Compounding": sim_weekly_reset_compound
}

print(f"{'Metodo':<26} | {'Exito $10k':<12} | {'Ruina (<$10)':<12} | {'Mediana Final':<14} | {'Max Final':<12} | {'MDD Promedio'}")
print("-" * 90)

for m_name, fn in methods.items():
    caps = 0
    ruins = 0
    finals = []
    mdds = []
    days_to_caps = []
    
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
        res = fn(all_events, match_idx, days=60)
        if res["hit_cap"]:
            caps += 1
            days_to_caps.append(res["days_to_cap"])
        if res["final_bankroll"] <= 10.0:
            ruins += 1
        finals.append(res["final_bankroll"])
        mdds.append(res["mdd"])
        
    avg_d = np.mean(days_to_caps) if days_to_caps else 0.0
    print(f"{m_name:<26} | {caps}/{total} ({caps/total*100:4.1f}%) | {ruins}/{total} ({ruins/total*100:4.1f}%) | ${np.median(finals):10.2f}   | ${np.max(finals):10.2f} | {np.mean(mdds)*100:5.1f}%")
