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
from live_auditor_engine import PatternStrengthAuditor

print("=" * 105)
print("🎯 MOTOR DE BACKTEST REALISTA: STAKE OSCILANTE ~$1.00 USD SEGÚN FUERZA DEL PATRÓN (2 AÑOS / 110 SEMANAS)")
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
    print(f"  • {r_name:<18}: {len(df):>5} sorteos ({df.iloc[0]['fecha']} a {df.iloc[-1]['fecha']})")

# 1. Generar eventos cronológicos sin look-ahead
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
        prev_num = nums[i - 1]

        if d != cur_d:
            cur_d = d
            seen_today = set()
            prev_was_repeat = False

        rec_set = set(nums[i - rec_w : i])
        raw_cands = [nums[i - l] for l in lags if i - l >= 0]
        cands_lag = sorted(list((set(raw_cands) - rec_set) - blacklist))

        skip_anti_cluster = bool(use_anti_cluster and prev_was_repeat)

        # Canal A: Disparo de Canasta por Lags Armónicos
        if cands_lag and not skip_anti_cluster:
            hit_lag = (actual in cands_lag)
            if streak in target_streaks:
                events.append({
                    "dt": dts[i],
                    "fecha": d,
                    "hora": h,
                    "ruleta": r_name,
                    "channel": "Canal_A_Lag",
                    "cands": cands_lag,
                    "actual": actual,
                    "actual_anim": animals[i],
                    "hit": hit_lag,
                    "payout": payout,
                    "trigger_misses": trigger_misses,
                    "idx": i
                })
                if hit_lag:
                    trigger_misses = 0
                else:
                    trigger_misses += 1
            streak = 0 if hit_lag else streak + 1
        elif cands_lag and skip_anti_cluster:
            hit_lag = (actual in cands_lag)
            streak = 0 if hit_lag else streak + 1
            if streak in target_streaks:
                trigger_misses += 1

        # Canal B: Disparo Markov Sniper Mono-Animal con Memoria Selectiva
        markov_target = markov_snipers.get(prev_num)
        if markov_target and markov_target not in rec_set and markov_target not in blacklist:
            m_hit = (actual == markov_target)
            events.append({
                "dt": dts[i],
                "fecha": d,
                "hora": h,
                "ruleta": r_name,
                "channel": "Canal_B_Markov",
                "cands": [markov_target],
                "actual": actual,
                "actual_anim": animals[i],
                "hit": m_hit,
                "payout": payout,
                "trigger_misses": 1,
                "idx": i
            })

        is_repeat_now = (actual in seen_today)
        seen_today.add(actual)
        prev_was_repeat = is_repeat_now

events.sort(key=lambda x: x["dt"])
print(f"\n✅ Total de disparos calificados generados: {len(events)} operaciones.")

# 2. Simulación de Bankroll con Sizing Oscilante ~$1.00 USD
initial_bankroll = 200.0
bankroll = initial_bankroll
peak = bankroll
max_dd_usd = 0.0
max_dd_pct = 0.0

total_invested = 0.0
total_collected = 0.0
gross_profits = 0.0
gross_losses = 0.0
wins_count = 0
total_bets_count = 0

start_dt = events[0]["dt"]
for ev in events:
    ev["week_idx"] = int((ev["dt"] - start_dt).total_seconds() // (7 * 86400))

total_weeks = events[-1]["week_idx"] + 1
weeks_dict = defaultdict(list)
for ev in events:
    weeks_dict[ev["week_idx"]].append(ev)

weekly_records = []
roulette_summary = defaultdict(lambda: {"bets": 0, "wins": 0, "invested": 0.0, "collected": 0.0, "pnl": 0.0})
channel_summary = defaultdict(lambda: {"bets": 0, "wins": 0, "invested": 0.0, "collected": 0.0, "pnl": 0.0})

# Mapeo rápido de datos para auditoría de fuerza en ventana rodante
series_nums = {r: all_series[r]["numero"].tolist() for r in all_series}

for w in range(total_weeks):
    w_start_b = bankroll
    w_events = weeks_dict.get(w, [])
    w_invested = 0.0
    w_collected = 0.0
    w_wins = 0
    w_bets = 0

    w_start_date = (start_dt + timedelta(days=w * 7)).strftime("%Y-%m-%d")
    w_end_date = (start_dt + timedelta(days=(w + 1) * 7 - 1)).strftime("%Y-%m-%d")

    for ev in w_events:
        r_name = ev["ruleta"]
        cfg = RULETAS_CONFIG[r_name]
        ch = ev["channel"]
        cands = ev["cands"]
        actual = ev["actual"]
        hit = ev["hit"]
        payout = ev["payout"]
        t_miss = ev["trigger_misses"]
        i_idx = ev["idx"]

        # Modulación del Stake alrededor de $1.00 USD según la fuerza del patrón:
        # Base: $1.00 USD
        # Si Canal B (Markov con Z alto): $1.25 a $1.35 USD
        # Si Canal A: Modula según tasa de acierto observada en ventana reciente de 60 sorteos:
        #   - Si fuerte (Z >= 1.5): $1.30 USD
        #   - Si normal (estable): $1.00 USD
        #   - Si fatigado (Z < -0.5): $0.70 USD
        #   - Si racha dulce (1-3 fallos): ajuste fino +$0.10
        if ch == "Canal_B_Markov":
            # Mono-animal sniper: alta convicción de Dirac
            stake_per_animal = 1.30
        else:
            # Canal A: Evaluación rápida de resonancia en ventana 60
            past_60 = series_nums[r_name][max(0, i_idx - 60):i_idx]
            lags = cfg["lags"]
            rec_w = cfg["rec_w"]
            p0 = len(cands) / float(cfg.get("k", 38))
            
            # Conteo rápido de aciertos retrospectivos
            hits_60 = 0
            opps_60 = 0
            for pos in range(len(past_60) - 1, max(0, len(past_60) - 30), -1):
                if pos - max(lags) >= 0:
                    opps_60 += 1
                    target_win = past_60[pos]
                    c_pool = set(past_60[pos - l] for l in lags if pos - l >= 0) - set(past_60[pos - rec_w:pos])
                    if target_win in c_pool:
                        hits_60 += 1
            
            obs_r = (hits_60 / opps_60) if opps_60 > 0 else p0
            ratio = obs_r / p0 if p0 > 0 else 1.0

            if ratio >= 1.25:
                base_mult = 1.25  # Fuerte
            elif ratio <= 0.75:
                base_mult = 0.70  # Fatigado
            else:
                base_mult = 1.00  # Normal

            # Ajuste por rebote
            rebound = 1.10 if (1 <= t_miss <= 3) else (0.90 if t_miss == 0 else 1.00)
            stake_per_animal = round(1.00 * base_mult * rebound, 2)
            stake_per_animal = max(0.60, min(1.40, stake_per_animal))

        total_cost = round(len(cands) * stake_per_animal, 2)

        if total_cost > bankroll:
            continue

        collected = round(stake_per_animal * payout, 2) if hit else 0.0
        pnl = round(collected - total_cost, 2)

        bankroll = round(bankroll + pnl, 2)
        if bankroll > peak:
            peak = bankroll

        dd_usd = peak - bankroll
        dd_pct = (dd_usd / peak * 100.0) if peak > 0 else 0.0

        if dd_usd > max_dd_usd:
            max_dd_usd = dd_usd
        if dd_pct > max_dd_pct:
            max_dd_pct = dd_pct

        total_bets_count += 1
        w_bets += 1
        w_invested += total_cost
        w_collected += collected
        total_invested += total_cost
        total_collected += collected

        if hit:
            wins_count += 1
            w_wins += 1
            gross_profits += pnl
        else:
            gross_losses += abs(pnl)

        # Resúmenes
        channel_summary[ch]["bets"] += 1
        if hit:
            channel_summary[ch]["wins"] += 1
        channel_summary[ch]["invested"] += total_cost
        channel_summary[ch]["collected"] += collected
        channel_summary[ch]["pnl"] += pnl

        roulette_summary[r_name]["bets"] += 1
        if hit:
            roulette_summary[r_name]["wins"] += 1
        roulette_summary[r_name]["invested"] += total_cost
        roulette_summary[r_name]["collected"] += collected
        roulette_summary[r_name]["pnl"] += pnl

    w_pnl = round(bankroll - w_start_b, 2)
    w_roi = round((w_pnl / w_invested * 100.0) if w_invested > 0 else 0.0, 2)

    weekly_records.append({
        "semana": w + 1,
        "fecha_inicio": w_start_date,
        "fecha_fin": w_end_date,
        "saldo_inicio": round(w_start_b, 2),
        "saldo_fin": round(bankroll, 2),
        "operaciones": w_bets,
        "aciertos": w_wins,
        "win_rate_pct": round((w_wins / w_bets * 100.0) if w_bets > 0 else 0.0, 1),
        "invertido": round(w_invested, 2),
        "cobrado": round(w_collected, 2),
        "pnl": w_pnl,
        "roi_pct": w_roi,
        "peak": round(peak, 2),
        "drawdown_pct": round(((peak - bankroll) / peak * 100.0) if peak > 0 else 0.0, 2)
    })

# Métricas Globales
net_pnl = round(bankroll - initial_bankroll, 2)
overall_roi = round(((total_collected - total_invested) / total_invested * 100.0) if total_invested > 0 else 0.0, 2)
profit_factor = round((gross_profits / gross_losses) if gross_losses > 0 else 999.0, 2)
overall_wr = round((wins_count / total_bets_count * 100.0) if total_bets_count > 0 else 0.0, 2)

winning_weeks = sum(1 for w in weekly_records if w["pnl"] > 0)
losing_weeks = sum(1 for w in weekly_records if w["pnl"] < 0)
even_weeks = sum(1 for w in weekly_records if w["pnl"] == 0)

# Sharpe & Sortino semanal
weekly_returns = [w["pnl"] / w["saldo_inicio"] for w in weekly_records if w["saldo_inicio"] > 0]
mean_ret = np.mean(weekly_returns)
std_ret = np.std(weekly_returns)
sharpe = round((mean_ret / std_ret * math.sqrt(52)) if std_ret > 0 else 0.0, 2)

downside = [r for r in weekly_returns if r < 0]
std_down = np.std(downside) if downside else 0.001
sortino = round((mean_ret / std_down * math.sqrt(52)) if std_down > 0 else 0.0, 2)

print("\n" + "=" * 95)
print("📊 RESULTADOS GLOBALES CON APUESTAS OSCILANTES ~$1.00 USD (2 AÑOS / 110 SEMANAS)")
print("=" * 95)
print(f"Capital Inicial:            ${initial_bankroll:,.2f} USD")
print(f"Capital Final Logrado:      ${bankroll:,.2f} USD")
print(f"Beneficio Neto (PnL Total): {'+' if net_pnl>=0 else ''}${net_pnl:,.2f} USD ({'+' if net_pnl>=0 else ''}{net_pnl/initial_bankroll*100:,.2f}%)")
print(f"Pico Máximo (ATH Peak):     ${peak:,.2f} USD")
print(f"Máximo Drawdown en USD:     -${max_dd_usd:,.2f} USD")
print(f"Máximo Drawdown en %:       {max_dd_pct:.2f}%")
print(f"Operaciones Realizadas:     {total_bets_count:,} apuestas")
print(f"Aciertos Totales:           {wins_count:,} aciertos (Win Rate: {overall_wr:.2f}%)")
print(f"Capital Total Invertido:    ${total_invested:,.2f} USD")
print(f"Capital Total Cobrado:      ${total_collected:,.2f} USD")
print(f"Retorno sobre Inversión:    +{overall_roi:.2f}%")
print(f"Profit Factor (PF):         {profit_factor:.2f}")
print(f"Sharpe Ratio Anualizado:    {sharpe:.2f}")
print(f"Sortino Ratio:              {sortino:.2f}")
print(f"Semanas Ganadoras:          {winning_weeks} de {total_weeks} ({winning_weeks/total_weeks*100:.1f}%)")
print(f"Semanas Perdedoras:         {losing_weeks} de {total_weeks} ({losing_weeks/total_weeks*100:.1f}%)")
print("=" * 95)

print("\nDesglose por Canal de Disparo:")
for ch, st in channel_summary.items():
    wr = (st['wins'] / st['bets'] * 100.0) if st['bets'] > 0 else 0.0
    roi = (st['pnl'] / st['invested'] * 100.0) if st['invested'] > 0 else 0.0
    print(f"  • {ch:<16}: {st['bets']:>5} ops | {st['wins']:>3} wins ({wr:.1f}%) | Inv: ${st['invested']:>8,.2f} | Cob: ${st['collected']:>8,.2f} | PnL: ${st['pnl']:>8,.2f} (ROI: {roi:+.2f}%)")

print("\nDesglose por Ruleta:")
for rn, st in roulette_summary.items():
    wr = (st['wins'] / st['bets'] * 100.0) if st['bets'] > 0 else 0.0
    roi = (st['pnl'] / st['invested'] * 100.0) if st['invested'] > 0 else 0.0
    print(f"  • {rn:<18}: {st['bets']:>5} ops | {st['wins']:>3} wins ({wr:.1f}%) | Inv: ${st['invested']:>8,.2f} | Cob: ${st['collected']:>8,.2f} | PnL: ${st['pnl']:>8,.2f} (ROI: {roi:+.2f}%)")

# Guardar resultados y curva semanal completa en JSON
output_data = {
    "summary": {
        "initial_bankroll": initial_bankroll,
        "final_bankroll": bankroll,
        "net_pnl": net_pnl,
        "roi_pct": overall_roi,
        "profit_factor": profit_factor,
        "win_rate": overall_wr,
        "total_bets": total_bets_count,
        "total_wins": wins_count,
        "total_invested": round(total_invested, 2),
        "total_collected": round(total_collected, 2),
        "peak": round(peak, 2),
        "max_dd_usd": round(max_dd_usd, 2),
        "max_dd_pct": round(max_dd_pct, 2),
        "sharpe": sharpe,
        "sortino": sortino,
        "total_weeks": total_weeks,
        "winning_weeks": winning_weeks,
        "losing_weeks": losing_weeks,
        "even_weeks": even_weeks
    },
    "channel_summary": dict(channel_summary),
    "roulette_summary": dict(roulette_summary),
    "weekly_records": weekly_records
}

with open(os.path.join(ROOT_DIR, "scratch", "backtest_fixed_1dollar_2y_results.json"), "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)
