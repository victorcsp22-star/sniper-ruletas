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
print("🎯 MOTOR DE BACKTEST REALISTA: STAKE FIJO $2.00 USD POR ANIMALITO (2 AÑOS / 110 SEMANAS)")
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

# 2. Simulación de Bankroll con Sizing Fijo de $2.00 USD POR ANIMALITO
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

STAKE_PER_ANIMAL = 2.00

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
        ch = ev["channel"]
        cands = ev["cands"]
        actual = ev["actual"]
        hit = ev["hit"]
        payout = ev["payout"]

        # Exactamente $2.00 USD por cada animalito apostado
        total_cost = round(len(cands) * STAKE_PER_ANIMAL, 2)

        if total_cost > bankroll:
            # Protocolo de seguridad si no hay bankroll suficiente
            continue

        collected = round(STAKE_PER_ANIMAL * payout, 2) if hit else 0.0
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
            gross_profits += (collected - total_cost)
        else:
            gross_losses += total_cost

        # Resumen por ruleta
        roulette_summary[r_name]["bets"] += 1
        roulette_summary[r_name]["invested"] += total_cost
        roulette_summary[r_name]["collected"] += collected
        roulette_summary[r_name]["pnl"] += pnl
        if hit:
            roulette_summary[r_name]["wins"] += 1

        # Resumen por canal
        channel_summary[ch]["bets"] += 1
        channel_summary[ch]["invested"] += total_cost
        channel_summary[ch]["collected"] += collected
        channel_summary[ch]["pnl"] += pnl
        if hit:
            channel_summary[ch]["wins"] += 1

    w_pnl = round(w_collected - w_invested, 2)
    w_roi = (w_pnl / w_invested * 100.0) if w_invested > 0 else 0.0
    w_wr = (w_wins / w_bets * 100.0) if w_bets > 0 else 0.0
    w_end_b = bankroll

    weekly_records.append({
        "week_num": w + 1,
        "start_date": w_start_date,
        "end_date": w_end_date,
        "start_bankroll": round(w_start_b, 2),
        "bets": w_bets,
        "wins": w_wins,
        "win_rate": round(w_wr, 2),
        "invested": round(w_invested, 2),
        "collected": round(w_collected, 2),
        "pnl": round(w_pnl, 2),
        "roi": round(w_roi, 2),
        "end_bankroll": round(w_end_b, 2),
        "peak_bankroll": round(peak, 2),
        "max_dd_usd": round(max_dd_usd, 2),
        "max_dd_pct": round(max_dd_pct, 2)
    })

# 3. Métricas Financieras y Estadísticas
pnl_total = round(bankroll - initial_bankroll, 2)
roi_total = round(pnl_total / total_invested * 100.0, 2) if total_invested > 0 else 0.0
pf = round(gross_profits / gross_losses, 2) if gross_losses > 0 else 999.0
wr_total = round(wins_count / total_bets_count * 100.0, 2) if total_bets_count > 0 else 0.0

weekly_pnls = [rec["pnl"] for rec in weekly_records]
pos_weeks = [rec for rec in weekly_records if rec["pnl"] > 0]
neg_weeks = [rec for rec in weekly_records if rec["pnl"] < 0]
neutral_weeks = [rec for rec in weekly_records if rec["pnl"] == 0]

mean_pnl = np.mean(weekly_pnls)
std_pnl = np.std(weekly_pnls)
sharpe = round((mean_pnl / std_pnl) * math.sqrt(52), 2) if std_pnl > 0 else 0.0

neg_pnls = [p for p in weekly_pnls if p < 0]
downside_std = np.std(neg_pnls) if neg_pnls else 0.001
sortino = round((mean_pnl / downside_std) * math.sqrt(52), 2) if downside_std > 0 else 0.0

print("\n" + "=" * 105)
print("📊 RESUMEN EJECUTIVO GLOBAL ($2.00 USD POR ANIMALITO):")
print("=" * 105)
print(f"  • Capital Inicial:            ${initial_bankroll:.2f} USD")
print(f"  • Capital Final Acumulado:    ${bankroll:.2f} USD")
print(f"  • Beneficio Neto (PnL):       +${pnl_total:.2f} USD ({(pnl_total/initial_bankroll*100.0):+.2f}%)")
print(f"  • ATH Peak:                   ${peak:.2f} USD")
print(f"  • Máximo Drawdown en USD:     -${max_dd_usd:.2f} USD")
print(f"  • Máximo Drawdown en %:       {max_dd_pct:.2f}%")
print(f"  • Total de Operaciones:       {total_bets_count:,} apuestas")
print(f"  • Aciertos Totales:           {wins_count:,} ({wr_total:.2f}%)")
print(f"  • Capital Invertido:          ${total_invested:,.2f} USD")
print(f"  • Capital Cobrado:            ${total_collected:,.2f} USD")
print(f"  • Retorno sobre Inv (ROI):    {roi_total:+.2f}%")
print(f"  • Profit Factor:              {pf:.2f}")
print(f"  • Sharpe Ratio Anualizado:    {sharpe:.2f}")
print(f"  • Sortino Ratio Anualizado:   {sortino:.2f}")
print(f"  • Semanas Positivas:          {len(pos_weeks)} ({len(pos_weeks)/len(weekly_records)*100.0:.1f}%)")
print(f"  • Semanas Negativas:          {len(neg_weeks)} ({len(neg_weeks)/len(weekly_records)*100.0:.1f}%)")
print(f"  • Semanas Neutras:            {len(neutral_weeks)}")

print("\n" + "=" * 105)
print("🎯 DESGLOSE POR RULETA ($2.00 FIJOS POR ANIMALITO):")
print("=" * 105)
for r_name, s in sorted(roulette_summary.items(), key=lambda x: x[1]["pnl"], reverse=True):
    wr = (s["wins"] / s["bets"] * 100.0) if s["bets"] > 0 else 0.0
    roi = (s["pnl"] / s["invested"] * 100.0) if s["invested"] > 0 else 0.0
    print(f"  • {r_name:<18}: {s['bets']:>5} ops | {s['wins']:>3} wins ({wr:>5.1f}%) | Inv: ${s['invested']:>8.2f} | Cob: ${s['collected']:>8.2f} | PnL: {s['pnl']:>+9.2f} USD | ROI: {roi:>+6.1f}%")

print("\n" + "=" * 105)
print("🎯 DESGLOSE POR CANAL ($2.00 FIJOS POR ANIMALITO):")
print("=" * 105)
for ch, s in sorted(channel_summary.items(), key=lambda x: x[1]["pnl"], reverse=True):
    wr = (s["wins"] / s["bets"] * 100.0) if s["bets"] > 0 else 0.0
    roi = (s["pnl"] / s["invested"] * 100.0) if s["invested"] > 0 else 0.0
    print(f"  • {ch:<20}: {s['bets']:>5} ops | {s['wins']:>3} wins ({wr:>5.1f}%) | Inv: ${s['invested']:>8.2f} | Cob: ${s['collected']:>8.2f} | PnL: {s['pnl']:>+9.2f} USD | ROI: {roi:>+6.1f}%")

# Guardar resultados para generar artefacto
out_data = {
    "initial_bankroll": initial_bankroll,
    "final_bankroll": bankroll,
    "pnl_total": pnl_total,
    "roi_total": roi_total,
    "profit_factor": pf,
    "sharpe": sharpe,
    "sortino": sortino,
    "max_dd_usd": max_dd_usd,
    "max_dd_pct": max_dd_pct,
    "total_bets": total_bets_count,
    "total_wins": wins_count,
    "win_rate": wr_total,
    "total_invested": total_invested,
    "total_collected": total_collected,
    "pos_weeks": len(pos_weeks),
    "neg_weeks": len(neg_weeks),
    "neutral_weeks": len(neutral_weeks),
    "roulette_summary": roulette_summary,
    "channel_summary": channel_summary,
    "weekly_records": weekly_records
}

out_path = os.path.join(ROOT_DIR, "scratch", "backtest_fixed_2dollars_2y_results.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out_data, f, indent=2, ensure_ascii=False)

print(f"\n💾 Archivo de resultados guardado en: {out_path}")
