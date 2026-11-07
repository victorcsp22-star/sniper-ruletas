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
from live_auditor_engine import PatternStrengthAuditor
from config import RULETAS_CONFIG

START_DT = datetime(2026, 10, 17, 9, 47, 0)

all_series = {}
for r_name, cfg in RULETAS_CONFIG.items():
    if not cfg.get("active", True) or "rec_w" not in cfg:
        continue
    df = pd.read_csv(cfg["file"], dtype={"numero": str})
    df["numero"] = df["numero"].astype(str).str.strip()
    df["animal"] = df["animal"].astype(str).str.strip()
    df["fecha"] = df["fecha"].astype(str).str.strip()
    df["hora"] = df["hora"].astype(str).str.strip()
    df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
    df = df.dropna(subset=["sort_dt"]).sort_values("sort_dt").reset_index(drop=True)
    all_series[r_name] = df

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

# Precomputar el estado hasta START_DT para cada ruleta
roulette_state = {}
for r_name, df in all_series.items():
    cfg = RULETAS_CONFIG[r_name]
    lags = cfg["lags"]
    rec_w = cfg["rec_w"]
    bl = set(cfg["blacklist"])
    pre_df = df[df["sort_dt"] < START_DT].copy()
    nums_pre = pre_df["numero"].tolist()
    
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
        cands = sorted(list((cand_pool - rec_set) - bl))

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
inhibited_count = 0

trades = []

target_mdd = 0.32
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

    if dt >= cycle_start_dt + timedelta(days=7):
        cycle_num += 1
        cycle_start_dt = cycle_start_dt + timedelta(days=7)
        cycle_base = bankroll

    r_st = roulette_state[r_name]

    if d != r_st["cur_date"]:
        r_st["cur_date"] = d
        r_st["seen_today"] = set()
        r_st["prev_was_repeat"] = False

    # 1. EVALUAR APUESTA PENDIENTE
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
            if bet["channel"] == "LAG":
                r_st["trigger_misses"] = 0
                r_st["streak"] = 0
        else:
            losses += 1
            if bet["channel"] == "LAG":
                r_st["trigger_misses"] += 1
                r_st["streak"] += 1

        trade_record = {
            "fecha": d,
            "hora": h,
            "ruleta": r_name,
            "candidatos": cands_str,
            "cands_count": len(cands),
            "zona_patron": smart_label,
            "smart_mult": bet.get("combined_mult", 1.0),
            "stake_unit": stake_unit,
            "total_bet": cost,
            "resultado": f"[{num}] {anim}",
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
        nums_all = df_r["numero"].tolist()
        rec_set = set(nums_all[g_idx - cfg["rec_w"] : g_idx])
        raw_cands = [nums_all[g_idx - l] for l in cfg["lags"] if g_idx - l >= 0]
        cands_org = sorted(list((set(raw_cands) - rec_set) - set(cfg["blacklist"])))
        if cands_org and not (cfg["anti_clustering"] and r_st["prev_was_repeat"]):
            hit_org = (num in cands_org)
            if hit_org:
                r_st["streak"] = 0
            else:
                r_st["streak"] += 1

    is_repeat_now = (num in r_st["seen_today"])
    r_st["seen_today"].add(num)
    r_st["prev_was_repeat"] = is_repeat_now

    # 2. GENERAR CANDIDATOS Y AUDITAR
    curr_dd = (peak - bankroll) / peak if peak > 0 else 0.0
    damping = max(0.15, 1.0 - (curr_dd / target_mdd))
    eff_kelly = base_kelly * damping

    cycle_pnl = bankroll - cycle_base
    cb_active = bool(cycle_pnl <= -cycle_base * cb_limit)
    is_quar = bool(r_st["trigger_misses"] >= 20)

    # Canal B: Markov Mono-Animal
    markov_target = cfg["markov_snipers"].get(num)
    nums_all = df_r["numero"].tolist()
    rec_set = set(nums_all[g_idx + 1 - cfg["rec_w"] : g_idx + 1])
    is_markov = (markov_target is not None and markov_target not in rec_set and markov_target not in cfg["blacklist"])

    # Canal A: Lag Sniper
    raw_cands = [nums_all[g_idx + 1 - l] for l in cfg["lags"] if g_idx + 1 - l >= 0]
    cands_lag = sorted(list((set(raw_cands) - rec_set) - set(cfg["blacklist"])))
    skip_ac = (cfg["anti_clustering"] and r_st["prev_was_repeat"])
    is_lag = (r_st["streak"] in cfg["target_streaks"] and not cb_active and not is_quar and not skip_ac and len(cands_lag) > 0)

    if is_markov or is_lag:
        # Prioridad de disparo: Si ambos se activan, Markov o Lag se ejecutan
        channel = "MARKOV" if is_markov else "LAG"
        cands_next = [markov_target] if is_markov else cands_lag
        bet_channel = "⚡ MARKOV SNIPER" if is_markov else "🎯 LAG SNIPER"

        df_past = df_r.iloc[:g_idx+1]
        strength_res = PatternStrengthAuditor.audit(r_name, cands_next, df_past, cfg, window_draws=60)
        auditor_mult = strength_res["capital_multiplier"]

        if auditor_mult == 0.0:
            inhibited_count += 1
            r_st["pending_bet"] = None
        else:
            t_miss = r_st["trigger_misses"] if channel == "LAG" else 1
            smart_mult = 1.25 if (1 <= t_miss <= 3) else (0.85 if t_miss == 0 else 1.0)
            
            combined_mult = smart_mult * auditor_mult
            base_f = cfg["f_unit"] if channel == "LAG" else (cfg["f_unit"] * 0.75)
            base_stake = max(0.10, round(cycle_base * base_f * eff_kelly, 2))
            final_stake_unit = max(0.10, round(base_stake * combined_mult, 2))
            cost = round(len(cands_next) * final_stake_unit, 2)

            num_to_anim = {str(row["numero"]): row["animal"] for _, row in df_r.iloc[:g_idx+1].iterrows()}
            cands_str = ", ".join([f"#{c} {num_to_anim.get(c, '')}" for c in cands_next])

            r_st["pending_bet"] = {
                "channel": channel,
                "cands": cands_next,
                "cands_str": cands_str,
                "cost": cost,
                "stake_unit": final_stake_unit,
                "payout": cfg["payout"],
                "smart_label": f"{bet_channel} | {strength_res['badge']} | Mult {combined_mult:.2f}x",
                "combined_mult": combined_mult
            }

print("\n" + "=" * 90)
print("📊 RESULTADOS DEL NUEVO SISTEMA ESPECIALIZADO EN EL PERÍODO EN VIVO")
print("=" * 90)
print(f"Período:                    17-Oct 09:47 AM hasta {chrono_events[-1]['dt']}")
print(f"Capital Inicial:            ${initial_bankroll:,.2f} USD")
print(f"Capital Final Hoy:          ${bankroll:,.2f} USD")
print(f"ATH Peak:                   ${peak:,.2f} USD")
print(f"Beneficio Neto (PnL):       {'+' if bankroll>=initial_bankroll else ''}${bankroll - initial_bankroll:,.2f} USD ({'+' if bankroll>=initial_bankroll else ''}{(bankroll - initial_bankroll)/initial_bankroll*100:.2f}%)")
print(f"Operaciones Realizadas:     {len(trades)}")
print(f"Aciertos / Fallos:          {wins} Aciertos / {losses} Fallos")
print(f"Tasa de Acierto:            {(wins/len(trades)*100 if trades else 0):.2f}%")
print(f"Capital Total Invertido:    ${total_invested:,.2f} USD")
print(f"Capital Total Cobrado:      ${total_collected:,.2f} USD")
print(f"ROI sobre Inversión:        {((total_collected - total_invested)/total_invested*100 if total_invested else 0):.2f}%")
print(f"Profit Factor:              {(total_collected/total_invested if total_invested else 0):.2f}")
print(f"Máximo Drawdown:            {max_dd*100:.2f}%")
print("=" * 90)

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
