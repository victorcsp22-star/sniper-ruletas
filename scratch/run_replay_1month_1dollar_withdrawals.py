import os
import sys
import json
import math
from collections import defaultdict
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = r"C:\Users\victo\nuevas_ruletas"
sys.path.append(ROOT_DIR)

from config import RULETAS_CONFIG

print("=" * 105)
print("🎯 REPLAY DETERMINISTA 1 MES: $1.00 FIJO POR ANIMAL CON RETIRO SEMANAL DE GANANCIAS")
print("=" * 105)

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

# Filtrar eventos desde hace exactamente 1 mes: 2026-09-30 00:00:00
START_DATE = "2026-09-30"
INITIAL_BASE_BANKROLL = 200.00
STAKE_PER_ANIMAL = 1.00

# 1. Generar todos los eventos cronológicos sin look-ahead
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
        dt = dts[i]
        prev_num = nums[i - 1]

        if d != cur_d:
            cur_d = d
            seen_today = set()
            prev_was_repeat = False

        rec_set = set(nums[i - rec_w : i])
        raw_cands = [nums[i - l] for l in lags if i - l >= 0]
        cands_lag = sorted(list((set(raw_cands) - rec_set) - blacklist))

        skip_anti_cluster = bool(use_anti_cluster and prev_was_repeat)

        lag_triggered = bool(cands_lag and not skip_anti_cluster and streak in target_streaks)
        markov_target = markov_snipers.get(prev_num)
        markov_triggered = bool(markov_target and markov_target not in rec_set and markov_target not in blacklist)

        # Si el sorteo ocurrió a partir del 2026-09-30, registrar evento de operación
        if d >= START_DATE:
            # Modelo de producción del bot: Prioridad a Markov Sniper mono-animal si coincide
            if markov_triggered:
                hit_m = (actual == markov_target)
                events.append({
                    "dt": dt,
                    "fecha": d,
                    "hora": h,
                    "ruleta": r_name,
                    "channel": "Canal_B_Markov",
                    "cands": [markov_target],
                    "actual": actual,
                    "actual_anim": animals[i],
                    "hit": hit_m,
                    "payout": payout,
                    "idx": i
                })
            elif lag_triggered:
                hit_lag = (actual in cands_lag)
                events.append({
                    "dt": dt,
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

        # Actualizar rachas de forma continua (para mantener integridad antes y después del corte)
        if cands_lag and not skip_anti_cluster:
            hit_lag = (actual in cands_lag)
            streak = 0 if hit_lag else streak + 1
        elif cands_lag and skip_anti_cluster:
            hit_lag = (actual in cands_lag)
            streak = 0 if hit_lag else streak + 1

        is_repeat_now = (actual in seen_today)
        seen_today.add(actual)
        prev_was_repeat = is_repeat_now

events.sort(key=lambda x: x["dt"])
print(f"✅ Total de disparos en el último mes ({START_DATE} a hoy): {len(events)} operaciones.")

# 2. Simulación de Bankroll con Retiro Semanal de Ganancias
# Ciclos de 7 días:
# Ciclo 1: 2026-09-30 a 2026-10-06
# Ciclo 2: 2026-10-07 a 2026-10-13
# Ciclo 3: 2026-10-14 a 2026-10-20
# Ciclo 4: 2026-10-21 a 2026-10-27
# Ciclo 5 (en curso): 2026-10-28 a 2026-10-30

start_dt = pd.to_datetime("2026-09-30 00:00:00")
for ev in events:
    diff_days = (ev["dt"] - start_dt).total_seconds() / 86400.0
    ev["cycle_num"] = int(diff_days // 7) + 1

cycle_dict = defaultdict(list)
for ev in events:
    cycle_dict[ev["cycle_num"]].append(ev)

total_cycles = max(cycle_dict.keys())

active_bankroll = INITIAL_BASE_BANKROLL
total_withdrawn = 0.0
total_invested = 0.0
total_collected = 0.0
total_wins = 0
total_ops = 0

weekly_reports = []
ledger_rows = []

for c_num in range(1, total_cycles + 1):
    c_events = cycle_dict.get(c_num, [])
    c_start_dt = start_dt + timedelta(days=(c_num - 1) * 7)
    c_end_dt = c_start_dt + timedelta(days=6, hours=23, minutes=59)
    c_start_date_str = c_start_dt.strftime("%Y-%m-%d")
    c_end_date_str = min(datetime.now().strftime("%Y-%m-%d"), c_end_dt.strftime("%Y-%m-%d"))

    c_start_bankroll = active_bankroll
    c_invested = 0.0
    c_collected = 0.0
    c_wins = 0
    c_ops = len(c_events)

    for ev in c_events:
        r_name = ev["ruleta"]
        cands = ev["cands"]
        actual = ev["actual"]
        hit = ev["hit"]
        payout = ev["payout"]

        cost = round(len(cands) * STAKE_PER_ANIMAL, 2)
        collected = round(STAKE_PER_ANIMAL * payout, 2) if hit else 0.0
        pnl = round(collected - cost, 2)

        active_bankroll = round(active_bankroll + pnl, 2)
        c_invested += cost
        c_collected += collected
        total_invested += cost
        total_collected += collected
        total_ops += 1

        if hit:
            c_wins += 1
            total_wins += 1

        # Mapeo a ledger
        num_str = f"#{actual} {ev['actual_anim']}"
        cond_str = "🟢 GANADA" if hit else "🔴 PERDIDA"
        ledger_rows.append({
            "fecha": ev["fecha"],
            "hora": ev["hora"],
            "ruleta": r_name,
            "candidatos": ", ".join(cands),
            "cands_count": len(cands),
            "zona_patron": f"{ev['channel']} ($1.00 fijo)",
            "smart_mult": 1.0,
            "stake_unit": STAKE_PER_ANIMAL,
            "total_bet": cost,
            "resultado": num_str,
            "condicion": cond_str,
            "cobrado": collected,
            "pnl": pnl,
            "saldo": active_bankroll,
            "peak": active_bankroll,
            "drawdown_pct": 0.0,
            "salido_num": actual,
            "salido_anim": ev["actual_anim"],
            "hit": hit,
            "inv": cost,
            "cob": collected,
            "bankroll": active_bankroll,
            "timestamp": f"{ev['fecha']} {ev['hora']}"
        })

    c_net_pnl = round(c_collected - c_invested, 2)
    c_roi = (c_net_pnl / c_invested * 100.0) if c_invested > 0 else 0.0
    c_wr = (c_wins / c_ops * 100.0) if c_ops > 0 else 0.0

    is_completed_cycle = (c_num < total_cycles)

    if is_completed_cycle:
        # Se retiran las ganancias netas si el ciclo cerró positivo
        if c_net_pnl > 0:
            withdrawn_amount = c_net_pnl
            total_withdrawn = round(total_withdrawn + withdrawn_amount, 2)
            # El saldo activo para la siguiente semana se reinicia a la base fija de $200
            active_bankroll = INITIAL_BASE_BANKROLL
            status_cycle = f"RETIRADO (+${withdrawn_amount:.2f} USD a Ganancias)"
        else:
            withdrawn_amount = 0.0
            status_cycle = "SIN RETIRO (Semana negativa)"
    else:
        # Ciclo actual en curso: las ganancias se mantienen acumulándose en mesa
        withdrawn_amount = 0.0
        status_cycle = "EN CURSO (En mesa)"

    weekly_reports.append({
        "cycle_num": c_num,
        "start_date": c_start_date_str,
        "end_date": c_end_date_str,
        "start_bankroll": c_start_bankroll,
        "ops": c_ops,
        "wins": c_wins,
        "win_rate": c_wr,
        "invested": c_invested,
        "collected": c_collected,
        "net_pnl": c_net_pnl,
        "roi": c_roi,
        "withdrawn": withdrawn_amount,
        "end_bankroll": active_bankroll,
        "status": status_cycle
    })

print("\n" + "=" * 105)
print("📊 RESUMEN SEMANAL DE RETIROS (ÚLTIMO MES - $1.00 FIJO):")
print("=" * 105)
for rep in weekly_reports:
    print(f"  • Ciclo {rep['cycle_num']} ({rep['start_date']} a {rep['end_date']}): {rep['ops']:>3} ops | {rep['wins']:>2} wins ({rep['win_rate']:>4.1f}%) | Inv: ${rep['invested']:>6.2f} | Cob: ${rep['collected']:>6.2f} | PnL: {rep['net_pnl']:>+7.2f} USD (ROI: {rep['roi']:>+5.1f}%) | {rep['status']}")

print("\n" + "=" * 105)
print("💰 BALANCE GENERAL CONSOLIDADO HOY:")
print("=" * 105)
capital_total_hoy = round(active_bankroll + total_withdrawn, 2)
beneficio_neto_total = round(capital_total_hoy - INITIAL_BASE_BANKROLL, 2)
print(f"  • Capital Base de Operación Inicial:     ${INITIAL_BASE_BANKROLL:.2f} USD")
print(f"  • Total Ganancias Retiradas (en mano):   ${total_withdrawn:.2f} USD")
print(f"  • Saldo Activo en Mesa Hoy:              ${active_bankroll:.2f} USD")
print(f"  • Capital Total Acumulado (Mesa + Mano): ${capital_total_hoy:.2f} USD")
print(f"  • Beneficio Neto Total en 1 Mes:         +${beneficio_neto_total:.2f} USD ({(beneficio_neto_total/INITIAL_BASE_BANKROLL*100):+.2f}%)")
print(f"  • Tasa de Acierto Global:                {total_wins}/{total_ops} ({(total_wins/total_ops*100):.2f}%)")

# Guardar en archivo para generar los artefactos y actualizar el bot
out_data = {
    "initial_base": INITIAL_BASE_BANKROLL,
    "active_bankroll": active_bankroll,
    "total_withdrawn": total_withdrawn,
    "total_capital": capital_total_hoy,
    "net_pnl_total": beneficio_neto_total,
    "total_ops": total_ops,
    "total_wins": total_wins,
    "total_invested": total_invested,
    "total_collected": total_collected,
    "weekly_reports": weekly_reports,
    "ledger_rows": ledger_rows
}

with open(os.path.join(ROOT_DIR, "scratch", "replay_1month_fixed1dollar_withdrawn.json"), "w", encoding="utf-8") as f:
    json.dump(out_data, f, indent=2, ensure_ascii=False)
