import os
import sys
import json
import math
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

sys.path.append(r"C:\Users\victo\nuevas_ruletas\scratch")
from research_backtest_audit import extract_events, simulate_portfolio, RULETAS_CONFIG

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

events_max, _ = extract_events(mode="maximizada")

# Let's inspect the 2-year simulation's weekly progression first
res_2y = simulate_portfolio(events_max, initial_bankroll=200.0, sizing_model="step_compounding", use_smart_momentum=True)
print(f"2Y total weeks: {res_2y['n_weeks']}")

# Now let's run a dedicated 1-Year Backtest (the last 52 weeks up to today, 2026-10-30)
# Let's find the exact date range for the last 52 weeks:
last_dt = events_max[-1]["dt"]
start_1y_dt = last_dt - timedelta(weeks=52)
events_1y = [e for e in events_max if e["dt"] >= start_1y_dt]

print(f"1Y Date Range: {events_1y[0]['dt']} to {events_1y[-1]['dt']}")
print(f"Events in 1Y: {len(events_1y)}")

# Run simulation starting with $200.00 USD 1 year ago:
# We need week_idx relative to events_1y[0]['dt']
def simulate_portfolio_granular_weeks(
    events,
    initial_bankroll=200.0,
    sizing_model="step_compounding",
    use_smart_momentum=True,
    cb_limit=0.15,
    target_mdd=0.32,
    decay_weeks=12,
    quarantine_misses=20,
    base_kelly=0.75,
    min_bet=0.10,
    flat_stake=1.0
):
    if not events:
        return None

    start_dt = events[0]["dt"]
    # Group by exact 7-day calendar periods
    for ev in events:
        ev["week_idx"] = int((ev["dt"] - start_dt).total_seconds() // (7 * 86400))

    total_weeks = events[-1]["week_idx"] + 1
    weeks_dict = {w: [] for w in range(total_weeks)}
    for ev in events:
        weeks_dict[ev["week_idx"]].append(ev)

    b = initial_bankroll
    peak = b
    max_mdd = 0.0
    decay_factor = (0.5 ** (1.0 / decay_weeks)) if decay_weeks > 0 else 1.0

    weekly_records = []

    for w in range(total_weeks):
        evs = weeks_dict[w]
        w_start_dt = start_dt + timedelta(days=w * 7)
        w_end_dt = w_start_dt + timedelta(days=6, hours=23, minutes=59)

        b_start = b

        if sizing_model == "step_compounding":
            peak = max(b_start, peak * decay_factor)
            curr_dd = (peak - b_start) / peak if peak > 0 else 0.0
            damping = max(0.15, 1.0 - (curr_dd / target_mdd)) if target_mdd > 0 else 1.0
            eff_kelly = base_kelly * damping
            weekly_stakes = {
                ev["ruleta"]: max(min_bet, round(b_start * ev["f_unit"] * eff_kelly, 2))
                for ev in evs
            }
        else:
            weekly_stakes = {ev["ruleta"]: flat_stake for ev in evs}

        pnl_w = 0.0
        inv_w = 0.0
        col_w = 0.0
        bets_w = 0
        wins_w = 0
        cb_tripped = False

        for ev in evs:
            if sizing_model == "step_compounding" and cb_limit > 0 and pnl_w <= -b_start * cb_limit:
                cb_tripped = True
                break

            if quarantine_misses > 0 and ev["trigger_misses"] >= quarantine_misses:
                continue

            base_stk = weekly_stakes[ev["ruleta"]]
            t_miss = ev["trigger_misses"]

            if use_smart_momentum:
                if 1 <= t_miss <= 3:
                    smart_mult = 1.25
                elif t_miss == 0:
                    smart_mult = 0.85
                else:
                    smart_mult = 1.00
            else:
                smart_mult = 1.00

            stk_unit = max(min_bet, round(base_stk * smart_mult, 2))
            bet_cost = round(stk_unit * ev["cost_units"], 2)

            if bet_cost > b:
                if b >= ev["cost_units"] * min_bet:
                    stk_unit = min_bet
                    bet_cost = round(stk_unit * ev["cost_units"], 2)
                else:
                    b = 0.0
                    break

            inv_w += bet_cost
            bets_w += 1

            if ev["hit"]:
                cob = round(stk_unit * ev["payout"], 2)
                pnl = round(cob - bet_cost, 2)
                wins_w += 1
            else:
                cob = 0.0
                pnl = -bet_cost

            col_w += cob
            pnl_w += pnl
            b = round(b + pnl, 2)

            if b > peak:
                peak = b
            dd = (peak - b) / peak if peak > 0 else 0.0
            if dd > max_mdd:
                max_mdd = dd

        w_ret = (pnl_w / b_start * 100.0) if b_start > 0 else 0.0
        curr_dd = (peak - b) / peak if peak > 0 else 0.0

        weekly_records.append({
            "week_num": w + 1,
            "start_date": w_start_dt.strftime("%Y-%m-%d"),
            "end_date": w_end_dt.strftime("%Y-%m-%d"),
            "bankroll_start": b_start,
            "bankroll_end": b,
            "bets": bets_w,
            "wins": wins_w,
            "win_rate": (wins_w / bets_w * 100.0) if bets_w > 0 else 0.0,
            "invested": inv_w,
            "collected": col_w,
            "pnl": pnl_w,
            "return_pct": w_ret,
            "drawdown_pct": curr_dd * 100.0,
            "cb_tripped": cb_tripped
        })

    return weekly_records, b, max_mdd * 100.0

# 1. Backtest empezando hace 1 año con $200 USD
records_1y_fresh, final_1y_fresh, mdd_1y_fresh = simulate_portfolio_granular_weeks(
    events_1y, initial_bankroll=200.0, sizing_model="step_compounding", use_smart_momentum=True
)

print(f"\n--- Backtest 1 Año Fresco (Base $200 USD hace 1 año) ---")
print(f"Semanas: {len(records_1y_fresh)}")
print(f"Capital Final: ${final_1y_fresh:,.2f} USD")
print(f"Max Drawdown: {mdd_1y_fresh:.2f}%")

# 2. Backtest de las últimas 52 semanas del ciclo acumulado de 2 años
# Veamos cómo evolucionaron las semanas 58 a 109 de la simulación de 2 años
records_2y_all, final_2y, mdd_2y = simulate_portfolio_granular_weeks(
    events_max, initial_bankroll=200.0, sizing_model="step_compounding", use_smart_momentum=True
)
print(f"\n--- Backtest 2 Años Completo (52 semanas más recientes) ---")
print(f"Total Semanas: {len(records_2y_all)}")
last_52_weeks_of_2y = records_2y_all[-52:]
print(f"Semana inicio ventana 1y: {last_52_weeks_of_2y[0]['week_num']} ({last_52_weeks_of_2y[0]['start_date']})")
print(f"Capital al inicio de la ventana 1y: ${last_52_weeks_of_2y[0]['bankroll_start']:,.2f} USD")
print(f"Capital al final: ${last_52_weeks_of_2y[-1]['bankroll_end']:,.2f} USD")

# Guardar ambos conjuntos para análisis exacto
with open(r"C:\Users\victo\nuevas_ruletas\scratch\weekly_backtest_1y.json", "w", encoding="utf-8") as f:
    json.dump({
        "fresh_1y": records_1y_fresh,
        "summary_fresh_1y": {
            "initial": 200.0,
            "final": final_1y_fresh,
            "max_dd": mdd_1y_fresh,
            "weeks": len(records_1y_fresh)
        },
        "last_52w_of_2y": last_52_weeks_of_2y
    }, f, indent=2)

print("\nGuardado en C:\\Users\\victo\\nuevas_ruletas\\scratch\\weekly_backtest_1y.json")
