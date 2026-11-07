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

# 1. Extraer todos los eventos cronológicos
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
                    "f_unit": f_unit
                })
            if hit:
                streak = 0
            else:
                streak += 1

all_events.sort(key=lambda x: x["dt"])
print(f"Total eventos cronológicos unificados: {len(all_events)}")
print(f"Rango de fechas: {all_events[0]['dt']} a {all_events[-1]['dt']}")

# Simulación de ventana de 60 días para diferentes multiplicadores de Kelly / métodos
def simulate_window(events, start_idx, days=60, kelly_multiplier=1.0, floor_pct=0.0, max_cap=10000.0, min_bet=0.10):
    start_dt = events[start_idx]["dt"]
    end_dt = start_dt + timedelta(days=days)
    
    bankroll = 200.0
    peak = 200.0
    hit_cap = False
    cap_dt = None
    min_bankroll = 200.0
    
    for idx in range(start_idx, len(events)):
        ev = events[idx]
        if ev["dt"] > end_dt:
            break
        
        # Sizing
        if floor_pct > 0.0:
            floor = (1.0 - floor_pct) * peak
            cushion = max(0.0, (bankroll - floor) / bankroll) if bankroll > 0 else 0.0
            damping = cushion ** 1.5
            stake_unit = max(min_bet, bankroll * ev["f_unit"] * kelly_multiplier * damping)
        else:
            stake_unit = max(min_bet, bankroll * ev["f_unit"] * kelly_multiplier)
        
        # Max single bet limit so bankroll is never negative
        total_stake = min(bankroll * 0.50, stake_unit * ev["cost_units"])
        unit_stake_actual = total_stake / ev["cost_units"]
        
        if ev["hit"]:
            cob = unit_stake_actual * ev["payout"]
            pnl = cob - total_stake
        else:
            pnl = -total_stake
            
        bankroll += pnl
        if bankroll < min_bankroll:
            min_bankroll = bankroll
            
        if bankroll > peak:
            peak = bankroll
            
        if bankroll >= max_cap and not hit_cap:
            hit_cap = True
            cap_dt = ev["dt"]
            bankroll = max_cap  # Take profit at cap
            break
            
        if bankroll <= 5.0:  # Ruina práctica
            break
            
    return {
        "start_dt": start_dt,
        "end_dt": end_dt,
        "final_bankroll": bankroll,
        "min_bankroll": min_bankroll,
        "hit_cap": hit_cap,
        "days_to_cap": (cap_dt - start_dt).total_seconds() / 86400.0 if hit_cap else None,
        "mdd": (peak - min_bankroll) / peak if peak > 0 else 1.0
    }

print("\n--- Evaluando Full Kelly Puro (1.0x) en todas las ventanas de 60 días (cada 15 días) ---")
# Probar diferentes factores de Kelly: 1.0x, 1.5x, 2.0x, 2.5x, 3.0x
start_dts = [all_events[0]["dt"] + timedelta(days=i*15) for i in range(45)]

for k_mult in [1.0, 1.5, 2.0, 2.5, 3.0, 4.0]:
    caps_hit = 0
    total_tested = 0
    final_b_list = []
    ruin_count = 0
    
    for s_dt in start_dts:
        # encontrar primer evento >= s_dt
        match_idx = None
        for i, ev in enumerate(all_events):
            if ev["dt"] >= s_dt:
                match_idx = i
                break
        if match_idx is None or match_idx >= len(all_events) - 50:
            continue
            
        res = simulate_window(all_events, match_idx, days=60, kelly_multiplier=k_mult, floor_pct=0.0)
        total_tested += 1
        if res["hit_cap"]:
            caps_hit += 1
        if res["final_bankroll"] <= 10.0:
            ruin_count += 1
        final_b_list.append(res["final_bankroll"])
        
    avg_f = np.mean(final_b_list)
    med_f = np.median(final_b_list)
    print(f"Kelly {k_mult:.1f}x: Alcanzó $10,000 en {caps_hit}/{total_tested} ventanas ({caps_hit/total_tested*100:.1f}%) | Ruina (<$10): {ruin_count}/{total_tested} ({ruin_count/total_tested*100:.1f}%) | Mediana: ${med_f:.2f} | Media: ${avg_f:.2f}")
