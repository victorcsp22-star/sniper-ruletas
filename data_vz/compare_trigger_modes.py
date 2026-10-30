"""
Comparativa profunda de los dos modos de Gatillo Post-Fallo 1 con $200 USD:
Modo 1: Disparo Único Sniper (streak == 1) -> Apuesta solo 1 vez tras el fallo.
Modo 2: Disparo Continuo (streak >= 1)     -> Apuesta tras el primer fallo continuamente hasta acertar.
"""

import os
import sys
import numpy as np
import pandas as pd

from backtest_brasil_200usd import load_and_prepare_datasets, CONFIG

datasets = load_and_prepare_datasets()
df_brasil = datasets["Lotto Brasil"]
df_bicho = datasets["Lotto Bicho"]

times_brasil = set(zip(df_brasil["fecha"], df_brasil["hora"]))
times_bicho = set(zip(df_bicho["fecha"], df_bicho["hora"]))
common_events = sorted(list(times_brasil.union(times_bicho)), 
                       key=lambda x: pd.to_datetime(x[0] + " " + x[1], format="%Y-%m-%d %I:%M %p"))

idx_brasil = {(row["fecha"], row["hora"]): i for i, row in df_brasil.iterrows()}
idx_bicho = {(row["fecha"], row["hora"]): i for i, row in df_bicho.iterrows()}
nums_brasil = df_brasil["numero"].tolist()
nums_bicho = df_bicho["numero"].tolist()

def simulate_mode(mode="single_shot", initial_bankroll=200.0, mdd_floor=0.40):
    b_fk = initial_bankroll
    b_gz = initial_bankroll
    peak_fk = initial_bankroll
    peak_gz = initial_bankroll
    mdd_fk = 0.0
    mdd_gz = 0.0

    streaks = {"Lotto Brasil": 0, "Lotto Bicho": 0}
    signals_count = {"Lotto Brasil": 0, "Lotto Bicho": 0}
    hits_count = {"Lotto Brasil": 0, "Lotto Bicho": 0}

    history_fk = [initial_bankroll]
    history_gz = [initial_bankroll]

    for cur_fecha, cur_hora in common_events:
        bets_this_hour = []

        # Brasil
        if (cur_fecha, cur_hora) in idx_brasil:
            i_b = idx_brasil[(cur_fecha, cur_hora)]
            if i_b >= 35:
                act = nums_brasil[i_b]
                hist = nums_brasil[:i_b]
                rec6 = set(hist[-6:])
                cands = list({hist[-l] for l in CONFIG["Lotto Brasil"]["lags"]} - rec6)
                hit = (act in cands)
                s = streaks["Lotto Brasil"]

                should_bet = (s == 1) if mode == "single_shot" else (s >= 1)
                if should_bet and len(cands) > 0:
                    bets_this_hour.append({
                        "roulette": "Lotto Brasil",
                        "cands_count": len(cands),
                        "hit": hit,
                        "payout": 37.0,
                        "f_unit": 0.00346
                    })
                streaks["Lotto Brasil"] = 0 if hit else (s + 1)

        # Bicho
        if (cur_fecha, cur_hora) in idx_bicho:
            i_bi = idx_bicho[(cur_fecha, cur_hora)]
            if i_bi >= 35:
                act = nums_bicho[i_bi]
                hist = nums_bicho[:i_bi]
                rec6 = set(hist[-6:])
                cands = list({hist[-l] for l in CONFIG["Lotto Bicho"]["lags"]} - rec6)
                hit = (act in cands)
                s = streaks["Lotto Bicho"]

                should_bet = (s == 1) if mode == "single_shot" else (s >= 1)
                if should_bet and len(cands) > 0:
                    bets_this_hour.append({
                        "roulette": "Lotto Bicho",
                        "cands_count": len(cands),
                        "hit": hit,
                        "payout": 35.0,
                        "f_unit": 0.00569
                    })
                streaks["Lotto Bicho"] = 0 if hit else (s + 1)

        for b in bets_this_hour:
            r = b["roulette"]
            signals_count[r] += 1
            if b["hit"]:
                hits_count[r] += 1

            # Full Kelly
            stake_fk = max(0.10, b_fk * b["f_unit"])
            cost_fk = stake_fk * b["cands_count"]
            if b["hit"]:
                b_fk += (stake_fk * b["payout"]) - cost_fk
            else:
                b_fk = max(0.50, b_fk - cost_fk)
            if b_fk > peak_fk: peak_fk = b_fk
            dd_fk = (peak_fk - b_fk) / peak_fk
            if dd_fk > mdd_fk: mdd_fk = dd_fk
            history_fk.append(b_fk)

            # Grossman-Zhou
            floor_gz = (1.0 - mdd_floor) * peak_gz
            cushion = max(0.0, (b_gz - floor_gz) / b_gz) if b_gz > 0 else 0.0
            damping = cushion ** 1.5
            stake_gz = max(0.10, b_gz * b["f_unit"] * damping)
            cost_gz = stake_gz * b["cands_count"]
            if b["hit"]:
                b_gz += (stake_gz * b["payout"]) - cost_gz
            else:
                b_gz = max(0.50, b_gz - cost_gz)
            if b_gz > peak_gz: peak_gz = b_gz
            dd_gz = (peak_gz - b_gz) / peak_gz
            if dd_gz > mdd_gz: mdd_gz = dd_gz
            history_gz.append(b_gz)

    return {
        "mode": mode,
        "signals": signals_count,
        "hits": hits_count,
        "final_fk": b_fk,
        "mdd_fk": mdd_fk * 100.0,
        "final_gz": b_gz,
        "mdd_gz": mdd_gz * 100.0,
        "history_fk": history_fk,
        "history_gz": history_gz
    }

print("=== MODO 1: DISPARO ÚNICO SNIPER (streak == 1) ===")
res1 = simulate_mode("single_shot")
print(f"Señales Brasil: {res1['signals']['Lotto Brasil']} | Aciertos: {res1['hits']['Lotto Brasil']} ({res1['hits']['Lotto Brasil']/res1['signals']['Lotto Brasil']*100:.2f}%)")
print(f"Señales Bicho:  {res1['signals']['Lotto Bicho']} | Aciertos: {res1['hits']['Lotto Bicho']} ({res1['hits']['Lotto Bicho']/res1['signals']['Lotto Bicho']*100:.2f}%)")
print(f"FULL KELLY PURO    -> Final: ${res1['final_fk']:,.2f} USD | MDD: {res1['mdd_fk']:.2f}%")
print(f"GROSSMAN-ZHOU (40%)-> Final: ${res1['final_gz']:,.2f} USD | MDD: {res1['mdd_gz']:.2f}%")

print("\n=== MODO 2: DISPARO CONTINUO POST-FALLO 1 (streak >= 1) ===")
res2 = simulate_mode("continuous")
print(f"Señales Brasil: {res2['signals']['Lotto Brasil']} | Aciertos: {res2['hits']['Lotto Brasil']} ({res2['hits']['Lotto Brasil']/res2['signals']['Lotto Brasil']*100:.2f}%)")
print(f"Señales Bicho:  {res2['signals']['Lotto Bicho']} | Aciertos: {res2['hits']['Lotto Bicho']} ({res2['hits']['Lotto Bicho']/res2['signals']['Lotto Bicho']*100:.2f}%)")
print(f"FULL KELLY PURO    -> Final: ${res2['final_fk']:,.2f} USD | MDD: {res2['mdd_fk']:.2f}%")
print(f"GROSSMAN-ZHOU (40%)-> Final: ${res2['final_gz']:,.2f} USD | MDD: {res2['mdd_gz']:.2f}%")
