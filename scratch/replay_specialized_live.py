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

sys.path.append(ROOT_DIR)
from live_auditor_engine import LIVE_AUDITOR, PatternStrengthAuditor, RegimeShiftAuditor

RULETAS_CONFIG = {
    "Lotto Activo": {
        "file": os.path.join(VZ_DIR, "lotto_activo_2anios.csv"),
        "lags": [20, 18, 14],
        "target_streaks": [1],
        "rec_w": 6,
        "anti_clustering": True,
        "blacklist": [],
        "markov_snipers": {},
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
        "blacklist": [],
        "markov_snipers": {"11": "34"},
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
        "blacklist": [],
        "markov_snipers": {},
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
        "blacklist": ["75"],
        "markov_snipers": {"16": "39", "59": "57"},
        "payout": 60.0,
        "f_unit": 0.00680,
        "k": 77,
        "emoji": "🦇"
    },
    "Gatazo": {
        "file": os.path.join(ROOT_DIR, "gatazo.csv"),
        "lags": [35, 9, 20],
        "target_streaks": [1, 2],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": ["11"],
        "markov_snipers": {"30": "63", "48": "21"},
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
        "blacklist": ["4"],
        "markov_snipers": {"32": "35", "11": "00"},
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
        "blacklist": ["75"],
        "markov_snipers": {},
        "payout": 60.0,
        "f_unit": 0.00700,
        "k": 77,
        "emoji": "🧘‍♂️"
    }
}

START_DT = datetime(2026, 10, 17, 9, 47, 0)

all_series = {}
for r_name, cfg in RULETAS_CONFIG.items():
    df = pd.read_csv(cfg["file"])
    df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
    df = df.dropna(subset=["sort_dt"]).sort_values("sort_dt").reset_index(drop=True)
    all_series[r_name] = df

# Generar cronología unificada de todos los sorteos
events = []
for r_name, df in all_series.items():
    for idx, row in df.iterrows():
        events.append({
            "ruleta": r_name,
            "idx": idx,
            "dt": row["sort_dt"],
            "fecha": row["fecha"],
            "hora": row["hora"],
            "numero": str(row["numero"]).strip(),
            "animal": str(row["animal"]).strip()
        })

events = sorted(events, key=lambda x: x["dt"])

# Simulación
bankroll = 200.0
peak = 200.0
total_invested = 0.0
total_collected = 0.0
wins = 0
losses = 0

cycle_base = 200.0
cycle_num = 1
cycle_start = START_DT
next_cycle_boundary = cycle_start + timedelta(days=7)

trades = []
streaks = {r: 0 for r in RULETAS_CONFIG}
trigger_misses = {r: 0 for r in RULETAS_CONFIG}

print(f"Iniciando simulación del Sistema Especializado desde {START_DT}...")

for ev in events:
    r_name = ev["ruleta"]
    cfg = RULETAS_CONFIG[r_name]
    dt = ev["dt"]
    idx = ev["idx"]
    actual_num = ev["numero"]
    actual_anim = ev["animal"]
    df_r = all_series[r_name]

    # Gestión de ciclos semanales (sábado a sábado 10:00 AM)
    if dt >= next_cycle_boundary:
        cycle_num += 1
        cycle_base = max(100.0, bankroll)
        cycle_start = next_cycle_boundary
        next_cycle_boundary = cycle_start + timedelta(days=7)

    # Estado previo del sorteo
    if idx < max(cfg["lags"]) + max(cfg["rec_w"], 8):
        continue

    # Lógica de canal A (Lags)
    past_nums = df_r.iloc[:idx]["numero"].astype(str).str.strip().tolist()
    rec_set = set(past_nums[-cfg["rec_w"]:])
    raw_lags = [past_nums[-l] for l in cfg["lags"] if l <= len(past_nums)]
    c_set = (set(raw_lags) - rec_set) - set(cfg["blacklist"])
    c_lags = sorted(list(c_set))

    # Compuerta Anti-clustering
    is_ac_blocked = False
    if cfg["anti_clustering"] and idx >= 2:
        last_date = str(df_r.iloc[idx - 1]["fecha"]).strip()
        day_draws = df_r.iloc[:idx][df_r.iloc[:idx]["fecha"] == last_date]["numero"].astype(str).str.strip().tolist()
        if len(day_draws) >= 2 and day_draws[-1] in day_draws[:-1]:
            is_ac_blocked = True

    # Lógica de canal B (Markov Mono-Animal)
    last_num = past_nums[-1]
    markov_target = cfg["markov_snipers"].get(last_num)
    is_markov_trigger = (markov_target is not None and markov_target not in rec_set and markov_target not in cfg["blacklist"])

    # Disparo del Sniper
    r_streak = streaks[r_name]
    is_lag_trigger = (r_streak in cfg["target_streaks"] and not is_ac_blocked and len(c_lags) > 0)

    # Decisión de apuesta
    has_bet = False
    bet_type = ""
    cands = []
    
    if is_markov_trigger:
        has_bet = True
        bet_type = "MARKOV_SNIPER"
        cands = [markov_target]
    elif is_lag_trigger:
        has_bet = True
        bet_type = "LAG_SNIPER"
        cands = c_lags

    # Solo ejecutamos si el sorteo está en el periodo de operación en vivo
    if dt >= START_DT and has_bet:
        # Consulta a los Auditores en Vivo
        audit_res = LIVE_AUDITOR.audit_betting_opportunity(
            r_name=r_name,
            candidates=[{"numero": c, "animal": ""} for c in cands],
            base_stake_unit=cycle_base * cfg["f_unit"],
            df=df_r.iloc[:idx],
            cfg=cfg,
            state={"bankroll": bankroll, "peak_bankroll": peak},
            trigger_misses=trigger_misses[r_name]
        )
        
        mult = audit_res["strength_audit"]["capital_multiplier"]
        stake_u = round(max(0.10, cycle_base * cfg["f_unit"] * mult), 2)
        total_bet = round(len(cands) * stake_u, 2)
        
        hit = (actual_num in cands)
        cobrado = round(stake_u * cfg["payout"], 2) if hit else 0.0
        pnl = round(cobrado - total_bet, 2)

        bankroll = round(bankroll + pnl, 2)
        peak = max(peak, bankroll)
        total_invested = round(total_invested + total_bet, 2)
        total_collected = round(total_collected + cobrado, 2)

        if hit:
            wins += 1
        else:
            losses += 1

        dd_pct = ((peak - bankroll) / peak * 100.0) if peak > 0 else 0.0

        # Mapeo a nombre
        num_to_anim = {str(row["numero"]).strip(): str(row["animal"]).strip() for _, row in df_r.iloc[:idx+1].iterrows()}
        cands_str = ", ".join([f"#{c} {num_to_anim.get(c, '')}" for c in cands])

        trades.append({
            "fecha": ev["fecha"],
            "hora": ev["hora"],
            "ruleta": r_name,
            "tipo": bet_type,
            "candidatos": cands_str,
            "cands_count": len(cands),
            "zona_patron": f"{bet_type} | Mult {mult:.2f}x | {audit_res['strength_audit']['badge']}",
            "smart_mult": mult,
            "stake_unit": stake_u,
            "total_bet": total_bet,
            "resultado": f"[{actual_num}] {actual_anim}",
            "condicion": "🟢 GANADA" if hit else "🔴 PERDIDA",
            "cobrado": cobrado,
            "pnl": pnl,
            "saldo": bankroll,
            "peak": peak,
            "drawdown_pct": round(dd_pct, 2),
            "hit": hit
        })

    # Actualizar estado de rachas
    # Para el canal de lags estándar:
    if len(c_lags) > 0 and not is_ac_blocked:
        hit_lag = (actual_num in c_lags)
        if hit_lag:
            streaks[r_name] = 0
            trigger_misses[r_name] = 0
        else:
            streaks[r_name] = streaks[r_name] + 1
            if r_streak in cfg["target_streaks"]:
                trigger_misses[r_name] = trigger_misses[r_name] + 1
    elif len(c_lags) > 0 and is_ac_blocked:
        hit_lag = (actual_num in c_lags)
        streaks[r_name] = 0 if hit_lag else (streaks[r_name] + 1)

print("\n" + "=" * 80)
print(" RESULTADOS REPLAY DEL NUEVO SISTEMA ESPECIALIZADO EN EL PERIODO EN VIVO")
print("=" * 80)
print(f"Período: {START_DT} hasta {events[-1]['dt']}")
print(f"Capital Inicial: $200.00 USD")
print(f"Capital Final: ${bankroll:,.2f} USD")
print(f"Peak Alcanzado: ${peak:,.2f} USD")
print(f"PnL Neto: {'+' if bankroll>=200 else ''}${bankroll-200.0:,.2f} USD ({'+' if bankroll>=200 else ''}{(bankroll-200)/2:.2f}%)")
print(f"Total Operaciones: {len(trades)}")
print(f"Aciertos: {wins} | Fallos: {losses} | Win Rate: {(wins/len(trades)*100 if trades else 0):.2f}%")
print(f"Total Invertido: ${total_invested:,.2f} USD")
print(f"Total Cobrado: ${total_collected:,.2f} USD")
print(f"ROI sobre Inversión: {((total_collected - total_invested)/total_invested*100 if total_invested else 0):.2f}%")
print("=" * 80)

# Resumen por ruleta
df_trades = pd.DataFrame(trades)
if not df_trades.empty:
    summary_r = df_trades.groupby("ruleta").agg(
        ops=("pnl", "count"),
        wins=("hit", "sum"),
        inv=("total_bet", "sum"),
        cob=("cobrado", "sum"),
        pnl=("pnl", "sum")
    ).reset_index()
    summary_r["roi"] = (summary_r["pnl"] / summary_r["inv"] * 100).round(2)
    print("\nDesglose por Ruleta:")
    print(summary_r.to_string(index=False))

with open(os.path.join(ROOT_DIR, "scratch", "specialized_live_replay.json"), "w", encoding="utf-8") as f:
    json.dump({
        "bankroll": bankroll,
        "peak": peak,
        "total_invested": total_invested,
        "total_collected": total_collected,
        "wins": wins,
        "losses": losses,
        "trades": trades
    }, f, indent=2, ensure_ascii=False)
