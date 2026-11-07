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

print("=" * 100)
print("🚀 MOTOR DE BACKTEST HISTÓRICO: SISTEMA ESPECIALIZADO DE PRODUCCIÓN (2 AÑOS COMPLETOS)")
print("=" * 100)

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

# Generar cronología unificada de disparos (Canal A y Canal B) sin look-ahead
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
    f_unit = cfg.get("f_unit", 0.008)

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
                    "cost_units": len(cands_lag),
                    "cands": cands_lag,
                    "actual": actual,
                    "actual_anim": animals[i],
                    "hit": hit_lag,
                    "payout": payout,
                    "f_unit": f_unit,
                    "trigger_misses": trigger_misses
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
                "cost_units": 1,
                "cands": [markov_target],
                "actual": actual,
                "actual_anim": animals[i],
                "hit": m_hit,
                "payout": payout,
                "f_unit": f_unit * 0.75,
                "trigger_misses": 1
            })

        is_repeat_now = (actual in seen_today)
        seen_today.add(actual)
        prev_was_repeat = is_repeat_now

events.sort(key=lambda x: x["dt"])
print(f"\n✅ Total de oportunidades generadas cronológicamente: {len(events)} operaciones.")

# Simulación de Cartera con Step-Compounding Semanal y Control de Drawdown
initial_bankroll = 200.0
base_kelly = 0.75
target_mdd = 0.32
cb_limit = 0.15
decay_weeks = 12
min_bet = 0.10

start_dt = events[0]["dt"]
for ev in events:
    ev["week_idx"] = int((ev["dt"] - start_dt).total_seconds() // (7 * 86400))

total_weeks = events[-1]["week_idx"] + 1
weeks_dict = defaultdict(list)
for ev in events:
    weeks_dict[ev["week_idx"]].append(ev)

b = initial_bankroll
peak = b
max_mdd = 0.0
total_invested = 0.0
total_collected = 0.0
gross_profits = 0.0
gross_losses = 0.0
wins_count = 0
total_bets_count = 0

weekly_curve = []
channel_stats = defaultdict(lambda: {"bets": 0, "wins": 0, "invested": 0.0, "collected": 0.0, "pnl": 0.0})
roulette_stats = defaultdict(lambda: {"bets": 0, "wins": 0, "invested": 0.0, "collected": 0.0, "pnl": 0.0})

for w in range(total_weeks):
    w_start_bankroll = b
    w_events = weeks_dict.get(w, [])

    # Damping de Kelly Grossman-Zhou
    curr_dd = (peak - b) / peak if peak > 0 else 0.0
    gz_damping = max(0.15, 1.0 - (curr_dd / target_mdd))
    weekly_kelly = base_kelly * gz_damping

    w_invested = 0.0
    w_collected = 0.0
    w_cb_triggered = False

    for ev in w_events:
        if w_cb_triggered:
            break

        f_u = ev["f_unit"]
        # Inversión inteligente según racha
        t_miss = ev["trigger_misses"]
        smart_mult = 1.25 if (1 <= t_miss <= 3) else (0.85 if t_miss == 0 else 1.0)

        stake_unit = max(min_bet, round(w_start_bankroll * f_u * weekly_kelly * smart_mult, 2))
        cost = round(ev["cost_units"] * stake_unit, 2)

        if cost > b:
            continue

        hit = ev["hit"]
        payout = ev["payout"]
        collected = round(stake_unit * payout, 2) if hit else 0.0
        pnl = round(collected - cost, 2)

        b += pnl
        if b > peak:
            peak = b

        instant_dd = (peak - b) / peak if peak > 0 else 0.0
        if instant_dd > max_mdd:
            max_mdd = instant_dd

        total_bets_count += 1
        w_invested += cost
        w_collected += collected
        total_invested += cost
        total_collected += collected

        if pnl > 0:
            gross_profits += pnl
            wins_count += 1
        else:
            gross_losses += abs(pnl)

        # Estadísticas por canal
        ch = ev["channel"]
        channel_stats[ch]["bets"] += 1
        if hit:
            channel_stats[ch]["wins"] += 1
        channel_stats[ch]["invested"] += cost
        channel_stats[ch]["collected"] += collected
        channel_stats[ch]["pnl"] += pnl

        # Estadísticas por ruleta
        rn = ev["ruleta"]
        roulette_stats[rn]["bets"] += 1
        if hit:
            roulette_stats[rn]["wins"] += 1
        roulette_stats[rn]["invested"] += cost
        roulette_stats[rn]["collected"] += collected
        roulette_stats[rn]["pnl"] += pnl

        # Circuit breaker semanal (-15% del base semanal)
        if (b - w_start_bankroll) <= -w_start_bankroll * cb_limit:
            w_cb_triggered = True

    # Decaimiento pasivo del pico (Grossman-Zhou Peak Decay)
    if b < peak and decay_weeks > 0:
        decay_rate = 0.005
        peak = max(b, peak * (1.0 - decay_rate))

    w_pnl = b - w_start_bankroll
    weekly_curve.append({
        "week": w + 1,
        "start_b": round(w_start_bankroll, 2),
        "end_b": round(b, 2),
        "pnl": round(w_pnl, 2),
        "pct": round((w_pnl / w_start_bankroll * 100.0) if w_start_bankroll > 0 else 0.0, 2),
        "bets": len(w_events),
        "kelly": round(weekly_kelly, 3),
        "dd_pct": round(curr_dd * 100.0, 2),
        "cb_active": w_cb_triggered
    })

# Métricas Globales
net_pnl = b - initial_bankroll
profit_factor = (gross_profits / gross_losses) if gross_losses > 0 else 999.0
overall_roi = ((total_collected - total_invested) / total_invested * 100.0) if total_invested > 0 else 0.0
win_rate = (wins_count / total_bets_count * 100.0) if total_bets_count > 0 else 0.0
cagr_weekly = ((b / initial_bankroll) ** (1.0 / total_weeks) - 1.0) * 100.0 if total_weeks > 0 else 0.0

# Ratios de Riesgo
weekly_returns = [w["pct"] / 100.0 for w in weekly_curve]
mean_ret = np.mean(weekly_returns)
std_ret = np.std(weekly_returns) if len(weekly_returns) > 1 else 1.0
sharpe = (mean_ret / std_ret * math.sqrt(52)) if std_ret > 0 else 0.0

downside_returns = [r for r in weekly_returns if r < 0]
std_down = np.std(downside_returns) if len(downside_returns) > 1 else 0.001
sortino = (mean_ret / std_down * math.sqrt(52)) if std_down > 0 else 0.0

winning_weeks = sum(1 for w in weekly_curve if w["pnl"] > 0)

print("\n" + "=" * 90)
print("📊 RESULTADOS OFICIALES DEL BACKTEST HISTÓRICO DE 2 AÑOS (110 SEMANAS)")
print("=" * 90)
print(f"Capital Inicial:            ${initial_bankroll:,.2f} USD")
print(f"Capital Final Logrado:      ${b:,.2f} USD")
print(f"Beneficio Neto Total:       +${net_pnl:,.2f} USD (+{net_pnl/initial_bankroll*100:,.2f}%)")
print(f"Total Operaciones:          {total_bets_count:,} apuestas")
print(f"Total Aciertos:             {wins_count:,} aciertos (Win Rate: {win_rate:.2f}%)")
print(f"Capital Total Invertido:    ${total_invested:,.2f} USD")
print(f"Capital Total Cobrado:      ${total_collected:,.2f} USD")
print(f"Retorno sobre Inversión:    +{overall_roi:.2f}%")
print(f"Profit Factor:              {profit_factor:.2f}")
print(f"Máximo Drawdown (MDD):      {max_mdd*100:.2f}%")
print(f"Sharpe Ratio Anualizado:    {sharpe:.2f}")
print(f"Sortino Ratio:              {sortino:.2f}")
print(f"CAGR Semanal Promedio:      +{cagr_weekly:.2f}% / semana")
print(f"Semanas Ganadoras:          {winning_weeks} de {total_weeks} ({winning_weeks/total_weeks*100:.1f}%)")
print("=" * 90)

print("\nDesglose por Canal de Disparo:")
for ch, st in channel_stats.items():
    wr = (st['wins'] / st['bets'] * 100.0) if st['bets'] > 0 else 0.0
    roi = (st['pnl'] / st['invested'] * 100.0) if st['invested'] > 0 else 0.0
    print(f"  • {ch:<16}: {st['bets']:>5} ops | {st['wins']:>3} wins ({wr:.1f}%) | Inv: ${st['invested']:>12,.2f} | Cob: ${st['collected']:>12,.2f} | PnL: ${st['pnl']:>12,.2f} (ROI: {roi:+.2f}%)")

print("\nDesglose por Ruleta:")
for rn, st in roulette_stats.items():
    wr = (st['wins'] / st['bets'] * 100.0) if st['bets'] > 0 else 0.0
    roi = (st['pnl'] / st['invested'] * 100.0) if st['invested'] > 0 else 0.0
    print(f"  • {rn:<18}: {st['bets']:>5} ops | {st['wins']:>3} wins ({wr:.1f}%) | Inv: ${st['invested']:>12,.2f} | Cob: ${st['collected']:>12,.2f} | PnL: ${st['pnl']:>12,.2f} (ROI: {roi:+.2f}%)")

output_payload = {
    "initial_bankroll": initial_bankroll,
    "final_bankroll": round(b, 2),
    "net_pnl": round(net_pnl, 2),
    "total_bets": total_bets_count,
    "total_wins": wins_count,
    "win_rate": round(win_rate, 2),
    "total_invested": round(total_invested, 2),
    "total_collected": round(total_collected, 2),
    "overall_roi": round(overall_roi, 2),
    "profit_factor": round(profit_factor, 2),
    "max_mdd": round(max_mdd * 100.0, 2),
    "sharpe": round(sharpe, 2),
    "sortino": round(sortino, 2),
    "cagr_weekly": round(cagr_weekly, 2),
    "total_weeks": total_weeks,
    "winning_weeks": winning_weeks,
    "channel_stats": dict(channel_stats),
    "roulette_stats": dict(roulette_stats),
    "weekly_curve": weekly_curve
}

with open(os.path.join(ROOT_DIR, "scratch", "backtest_full_production_2y_results.json"), "w", encoding="utf-8") as f:
    json.dump(output_payload, f, indent=2, ensure_ascii=False)
