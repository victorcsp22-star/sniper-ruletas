import os
import sys
import json
import math
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = r"C:\Users\victo\nuevas_ruletas"
VZ_DIR = os.path.join(ROOT_DIR, "data_vz")

RULETAS_CONFIG = {
    "Lotto Activo": {
        "file": os.path.join(VZ_DIR, "lotto_activo_2anios.csv"),
        "lags": [20, 18, 14],
        "target_streaks": [1],
        "rec_w": 6,
        "anti_clustering": True,
        "payout": 30.0,
        "f_unit": 0.00900,
        "k": 38,
        "emoji": "🦁"
    },
    "La Granjita": {
        "file": os.path.join(VZ_DIR, "la_granjita_2anios.csv"),
        "lags": [15, 17],
        "target_streaks": [1],
        "rec_w": 9,
        "anti_clustering": False,
        "payout": 30.0,
        "f_unit": 0.00484,
        "k": 38,
        "emoji": "🐸"
    },
    "Ruleta Royal": {
        "file": os.path.join(VZ_DIR, "ruleta_royal_2anios.csv"),
        "lags": [16, 19, 31],
        "target_streaks": [1],
        "rec_w": 6,
        "anti_clustering": True,
        "payout": 30.0,
        "f_unit": 0.00826,
        "k": 38,
        "emoji": "👑"
    },
    "Guacharo Activo": {
        "file": os.path.join(VZ_DIR, "guacharo_activo_2anios.csv"),
        "lags": [31, 41, 25, 42, 35],
        "target_streaks": [1],
        "rec_w": 8,
        "anti_clustering": False,
        "payout": 60.0,
        "f_unit": 0.00680,
        "k": 77,
        "emoji": "🦇"
    },
    "Gatazo": {
        "file": os.path.join(ROOT_DIR, "gatazo.csv"),
        "lags": [35, 22, 20],
        "target_streaks": [1, 2],
        "rec_w": 6,
        "anti_clustering": False,
        "payout": 60.0,
        "f_unit": 0.00900,
        "k": 85,
        "emoji": "🐯"
    },
    "Mega Animal 40": {
        "file": os.path.join(ROOT_DIR, "mega_animal_40.csv"),
        "lags": [18, 21, 20],
        "target_streaks": [1],
        "rec_w": 8,
        "anti_clustering": False,
        "payout": 30.0,
        "f_unit": 0.00800,
        "k": 47,
        "emoji": "🦏"
    },
    "Monje Millonario": {
        "file": os.path.join(ROOT_DIR, "monje_millonario.csv"),
        "lags": [24, 42],
        "target_streaks": [1],
        "rec_w": 6,
        "anti_clustering": False,
        "payout": 60.0,
        "f_unit": 0.00700,
        "k": 77,
        "emoji": "🧘‍♂️"
    }
}

START_DT = datetime(2026, 10, 17, 9, 47, 0)
CYCLE_1_END = START_DT + timedelta(days=7) # 2026-10-24 09:47:00

# Load full history of each roulette to determine initial streak and lags causality
all_series = {}
for r_name, cfg in RULETAS_CONFIG.items():
    df = pd.read_csv(cfg["file"], dtype={"numero": str})
    df["numero"] = df["numero"].astype(str).str.strip()
    df["animal"] = df["animal"].astype(str).str.strip()
    df["fecha"] = df["fecha"].astype(str).str.strip()
    df["hora"] = df["hora"].astype(str).str.strip()
    df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
    df = df.dropna(subset=["sort_dt"]).sort_values("sort_dt").reset_index(drop=True)
    all_series[r_name] = df

# Collect all chronological draws across all 7 roulettes from START_DT forward
chrono_events = []
for r_name, df in all_series.items():
    sub_df = df[df["sort_dt"] >= START_DT].copy()
    for idx_row, row in sub_df.iterrows():
        chrono_events.append({
            "r_name": r_name,
            "dt": row["sort_dt"],
            "fecha": row["fecha"],
            "hora": row["hora"],
            "numero": row["numero"],
            "animal": row["animal"],
            "global_idx": idx_row
        })

chrono_events.sort(key=lambda x: x["dt"])
print(f"Total eventos cronológicos a procesar desde 17-Oct 09:47 AM: {len(chrono_events)}")

# Initialize roulette tracker states prior to START_DT
roulette_state = {}
for r_name, df in all_series.items():
    cfg = RULETAS_CONFIG[r_name]
    lags = cfg["lags"]
    rec_w = cfg["rec_w"]
    # Historical draws prior to START_DT
    pre_df = df[df["sort_dt"] < START_DT].copy()
    nums_pre = pre_df["numero"].tolist()
    
    # Calculate streak as of START_DT
    # Evaluate backward to find last hit
    streak = 0
    trigger_misses = 0
    cur_d = None
    seen_today = set()
    prev_was_repeat = False

    min_k = max(max(lags), rec_w) + 1
    for i in range(min_k, len(nums_pre)):
        act = nums_pre[i]
        d = pre_df.iloc[i]["fecha"]
        if d != cur_d:
            cur_d = d
            seen_today = set()
            prev_was_repeat = False

        rec_set = set(nums_pre[i - rec_w : i])
        cand_pool = set()
        for l in lags:
            if i - l >= 0:
                cand_pool.add(nums_pre[i - l])
        cands = sorted(list(cand_pool - rec_set))

        skip_ac = (cfg["anti_clustering"] and prev_was_repeat)
        if cands and not skip_ac:
            hit = (act in cands)
            if streak in cfg["target_streaks"]:
                if hit:
                    trigger_misses = 0
                else:
                    trigger_misses += 1
            streak = 0 if hit else streak + 1
        elif cands and skip_ac:
            hit = (act in cands)
            streak = 0 if hit else streak + 1
            if streak in cfg["target_streaks"]:
                trigger_misses += 1

        is_rep = (act in seen_today)
        seen_today.add(act)
        prev_was_repeat = is_rep

    roulette_state[r_name] = {
        "streak": streak,
        "trigger_misses": trigger_misses,
        "seen_today": set(),
        "cur_date": None,
        "prev_was_repeat": False,
        "pending_bet": None
    }
    print(f"Estado inicial al 17-Oct 09:47 AM -> {r_name}: Racha={streak}, Misses={trigger_misses}")

# Simulation variables
initial_bankroll = 200.0
bankroll = initial_bankroll
peak = bankroll
max_dd = 0.0

cycle_num = 1
cycle_base = bankroll
cycle_start_dt = START_DT
total_invested = 0.0
total_collected = 0.0
wins = 0
losses = 0

trades = []

target_mdd = 0.32
decay_weeks = 12
decay_factor = 0.5 ** (1.0 / decay_weeks)
base_kelly = 0.75
cb_limit = 0.15

for ev in chrono_events:
    r_name = ev["r_name"]
    cfg = RULETAS_CONFIG[r_name]
    dt = ev["dt"]
    d = ev["fecha"]
    h = ev["hora"]
    num = ev["numero"]
    anim = ev["animal"]
    g_idx = ev["global_idx"]
    df_r = all_series[r_name]

    # Check weekly cycle reset (Day 7 transition)
    if dt >= cycle_start_dt + timedelta(days=7):
        cycle_num += 1
        cycle_start_dt = cycle_start_dt + timedelta(days=7)
        cycle_base = bankroll
        print(f"\n🔄 CONSOLIDACIÓN DE CICLO: Inicio de Ciclo {cycle_num} el {dt.strftime('%Y-%m-%d %I:%M %p')} con Base ${cycle_base:,.2f} USD\n")

    r_st = roulette_state[r_name]

    # Reset intraday tracking if new day
    if d != r_st["cur_date"]:
        r_st["cur_date"] = d
        r_st["seen_today"] = set()
        r_st["prev_was_repeat"] = False

    # 1. EVALUAR APUESTA PENDIENTE SI EXISTÍA PARA ESTE SORTEO
    if r_st["pending_bet"] is not None:
        bet = r_st["pending_bet"]
        cands = bet["cands"]
        cands_str = bet["cands_str"]
        cost = bet["cost"]
        stake_unit = bet["stake_unit"]
        payout = bet["payout"]
        smart_label = bet["smart_label"]

        hit = (num in cands)
        cobrado = round(stake_unit * payout, 2) if hit else 0.0
        pnl = round(cobrado - cost, 2)

        bankroll = round(bankroll + pnl, 2)
        total_invested = round(total_invested + cost, 2)
        total_collected = round(total_collected + cobrado, 2)

        if bankroll > peak:
            peak = bankroll
        curr_dd = (peak - bankroll) / peak if peak > 0 else 0.0
        if curr_dd > max_dd:
            max_dd = curr_dd

        if hit:
            wins += 1
            r_st["trigger_misses"] = 0
            r_st["streak"] = 0
        else:
            losses += 1
            r_st["trigger_misses"] += 1
            r_st["streak"] += 1

        trade_record = {
            "fecha": d,
            "hora": h,
            "ruleta": r_name,
            "candidatos": cands_str,
            "cands_count": len(cands),
            "zona_patron": smart_label,
            "stake_unit": stake_unit,
            "total_bet": cost,
            "resultado": f"#{num} {anim}",
            "condicion": "🟢 GANADA" if hit else "🔴 PERDIDA",
            "cobrado": cobrado,
            "pnl": pnl,
            "saldo": bankroll,
            "peak": peak,
            "drawdown_pct": round(curr_dd * 100.0, 2),
            "hit": hit
        }
        trades.append(trade_record)
        r_st["pending_bet"] = None

    else:
        # Si no había apuesta pendiente pero el patrón acertó de forma orgánica, resetear racha
        # Verificar si este sorteo acierta con los candidatos causales
        nums_all = df_r["numero"].tolist()
        rec_set = set(nums_all[g_idx - cfg["rec_w"] : g_idx])
        raw_cands = [nums_all[g_idx - l] for l in cfg["lags"] if g_idx - l >= 0]
        cands_org = sorted(list(set(raw_cands) - rec_set))
        if cands_org and not (cfg["anti_clustering"] and r_st["prev_was_repeat"]):
            hit_org = (num in cands_org)
            if hit_org:
                r_st["streak"] = 0
            else:
                r_st["streak"] += 1

    # Actualizar estado de repetición intradía
    is_repeat_now = (num in r_st["seen_today"])
    r_st["seen_today"].add(num)
    r_st["prev_was_repeat"] = is_repeat_now

    # 2. GENERAR CANDIDATOS PARA EL PRÓXIMO SORTEO DE ESTA RULETA
    # Damping y Kelly dinámico
    curr_dd = (peak - bankroll) / peak if peak > 0 else 0.0
    damping = max(0.15, 1.0 - (curr_dd / target_mdd))
    eff_kelly = base_kelly * damping

    cycle_pnl = bankroll - cycle_base
    cb_active = bool(cycle_pnl <= -cycle_base * cb_limit)
    is_quar = bool(r_st["trigger_misses"] >= 20)

    # Revisar si se debe generar disparo para el siguiente sorteo
    if r_st["streak"] in cfg["target_streaks"] and not cb_active and not is_quar:
        nums_all = df_r["numero"].tolist()
        rec_set = set(nums_all[g_idx + 1 - cfg["rec_w"] : g_idx + 1])
        raw_cands = [nums_all[g_idx + 1 - l] for l in cfg["lags"] if g_idx + 1 - l >= 0]
        cands_next = sorted(list(set(raw_cands) - rec_set))

        skip_ac = (cfg["anti_clustering"] and r_st["prev_was_repeat"])

        if cands_next and not skip_ac:
            # Multiplicador Smart Rebound
            t_miss = r_st["trigger_misses"]
            if 1 <= t_miss <= 3:
                smart_mult = 1.25
                smart_desc = "Zona Dulce Rebote (1.25x)"
            elif t_miss == 0:
                smart_mult = 0.85
                smart_desc = "Zona Fatigada (0.85x)"
            else:
                smart_mult = 1.00
                smart_desc = "Zona Neutral (1.00x)"

            base_stake = max(0.10, round(cycle_base * cfg["f_unit"] * eff_kelly, 2))
            final_stake_unit = max(0.10, round(base_stake * smart_mult, 2))
            cost = round(len(cands_next) * final_stake_unit, 2)

            num_to_anim = {str(row["numero"]): row["animal"] for _, row in df_r.iloc[:g_idx+1].iterrows()}
            cands_str = ", ".join([f"#{c} {num_to_anim.get(c, '')}" for c in cands_next])

            r_st["pending_bet"] = {
                "cands": cands_next,
                "cands_str": cands_str,
                "cost": cost,
                "stake_unit": final_stake_unit,
                "payout": cfg["payout"],
                "smart_label": f"{smart_desc} | Kelly {eff_kelly:.2f}x"
            }

print("\n" + "=" * 90)
print("📊 RESULTADOS DE LA REPLAY AUDITADA (17-OCTUBRE A 30-OCTUBRE 2026 - ESTRATEGIA MAXIMIZADA)")
print("=" * 90)
print(f"Capital Inicial:            ${initial_bankroll:,.2f} USD (17-Oct 09:47 AM)")
print(f"Capital Final Actual (Hoy): ${bankroll:,.2f} USD (30-Oct 12:00 PM)")
print(f"Ganancia Neta (PnL):        {'+' if bankroll>=initial_bankroll else ''}${bankroll - initial_bankroll:,.2f} USD ({((bankroll/initial_bankroll)-1)*100:+.2f}%)")
print(f"ATH Dinámico (Peak):        ${peak:,.2f} USD")
print(f"Máximo Drawdown:            {max_dd*100:.2f}%")
print(f"Operaciones Ejecutadas:     {len(trades)} trades")
print(f"Aciertos:                   {wins} Ganadas ({wins/len(trades)*100:.2f}%)")
print(f"Fallos:                     {losses} Perdidas")
print(f"Total Invertido:            ${total_invested:,.2f} USD")
print(f"Total Cobrado:              ${total_collected:,.2f} USD")
print(f"ROI sobre Inversión:        {(total_collected - total_invested)/total_invested*100:.2f}%")
print(f"Profit Factor:              {(total_collected - total_invested + total_invested)/total_invested if total_invested>0 else 0:.2f}")

# Guardar en archivo scratch para validación
with open(r"C:\Users\victo\nuevas_ruletas\scratch\replay_summary.json", "w", encoding="utf-8") as f:
    json.dump({
        "bankroll": bankroll,
        "peak": peak,
        "max_dd_pct": max_dd * 100.0,
        "wins": wins,
        "losses": losses,
        "total_invested": total_invested,
        "total_collected": total_collected,
        "trades_count": len(trades),
        "trades": trades
    }, f, indent=2, ensure_ascii=False)
