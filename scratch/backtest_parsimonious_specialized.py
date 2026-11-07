"""
========================================================================================
 MOTOR DE BACKTESTING: SISTEMA MULTI-AGENTE PARSIMONIOSO CON TIROS SNIPER MARKOVIANOS
========================================================================================
Aplica el principio de parsimonia de canasta (Basket Parsimony):
 1. Canastas Ultra-Comprimidas por Lags Armónicos (Lotto [20,18,14], Granjita [15,17] rec9,
    Royal [16,19,31], Guácharo [31,41,25,42], Gatazo [35,9,20], Mega [18,21,20], Monje [24,42]).
 2. Purga estricta de Números Trampa (#75 en Guácharo, #11 en Gatazo).
 3. Gatillo Dual:
    - Canal A (Sniper Lag): Disparo estándar en Racha 1 de canasta comprimida.
    - Canal B (Sniper Markov Mono-Animal): Disparo directo a 1 SOLO animal cuando se detona
      una hiper-transición condicional certificada (Z >= 4.0):
      * Gatazo: Tras #30 Caimán -> #63 Cangrejo (13.89% prob a cuota 60x!).
      * Gatazo: Tras #48 Puercoespín -> #21 Gallo (11.36% prob a cuota 60x!).
      * Mega Animal: Tras #32 Ardilla -> #35 Jirafa (12.73% prob a cuota 30x!).
      * Mega Animal: Tras #11 Gato -> #00 Ballena (12.73% prob a cuota 30x!).
      * La Granjita: Tras #11 Gato -> #34 Venado (6.99% prob a cuota 30x!).
 4. Asignación de Capital: Step-compounding semanal con amortiguación de Kelly (Grossman-Zhou).
========================================================================================
"""

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
VZ_DIR = os.path.join(ROOT_DIR, "data_vz")

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
        "k": 38
    },
    "La Granjita": {
        "file": os.path.join(VZ_DIR, "la_granjita_2anios.csv"),
        "lags": [15, 17],
        "target_streaks": [1],
        "rec_w": 9,
        "anti_clustering": False,
        "blacklist": [],
        "markov_snipers": {"11": "34"},  # Z = +4.00, prob 6.99%
        "payout": 30.0,
        "f_unit": 0.00484,
        "k": 38
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
        "k": 37
    },
    "Guacharo Activo": {
        "file": os.path.join(VZ_DIR, "guacharo_activo_2anios.csv"),
        "lags": [31, 41, 25, 42, 35],
        "target_streaks": [1],
        "rec_w": 8,
        "anti_clustering": False,
        "blacklist": ["75"],  # Purgar número trampa
        "markov_snipers": {"16": "39", "59": "57"},  # Z = +4.46
        "payout": 60.0,
        "f_unit": 0.00680,
        "k": 77
    },
    "Gatazo": {
        "file": os.path.join(ROOT_DIR, "gatazo.csv"),
        "lags": [35, 9, 20],
        "target_streaks": [1, 2],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": ["11"],  # Purgar número trampa
        "markov_snipers": {"30": "63", "48": "21"},  # Z = +7.58, prob 13.89% y 11.36%
        "payout": 60.0,
        "f_unit": 0.00900,
        "k": 85
    },
    "Mega Animal 40": {
        "file": os.path.join(ROOT_DIR, "mega_animal_40.csv"),
        "lags": [18, 21, 20],
        "target_streaks": [1],
        "rec_w": 8,
        "anti_clustering": False,
        "blacklist": ["4"],
        "markov_snipers": {"32": "35", "11": "00"},  # Z = +5.92, prob 12.73%
        "payout": 30.0,
        "f_unit": 0.00800,
        "k": 47
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
        "k": 77
    }
}


def extract_parsimonious_events():
    events = []
    leak_count = 0

    for r_name, cfg in RULETAS_CONFIG.items():
        if not os.path.exists(cfg["file"]):
            continue
        df = pd.read_csv(cfg["file"], dtype={"numero": str})
        df["numero"] = df["numero"].astype(str).str.strip()
        df["fecha"] = df["fecha"].astype(str).str.strip()
        df["hora"] = df["hora"].astype(str).str.strip()
        df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        df = df.dropna(subset=["sort_dt"]).sort_values("sort_dt").reset_index(drop=True)

        nums = df["numero"].tolist()
        dates = df["fecha"].tolist()
        dts = df["sort_dt"].tolist()
        n_draws = len(nums)

        lags = cfg["lags"]
        rec_w = cfg["rec_w"]
        use_anti_cluster = cfg["anti_clustering"]
        blacklist = set(cfg["blacklist"])
        markov_snipers = cfg["markov_snipers"]
        payout = cfg["payout"]
        f_unit = cfg["f_unit"]
        target_streaks = cfg["target_streaks"]

        min_idx = max(max(lags), rec_w) + 10

        streak = 0
        trigger_misses = 0
        cur_date = None
        seen_today = set()
        prev_was_repeat = False

        for i in range(min_idx, n_draws):
            actual = nums[i]
            d = dates[i]
            prev_num = nums[i - 1]

            if d != cur_date:
                cur_date = d
                seen_today = set()
                prev_was_repeat = False

            rec_set = set(nums[i - rec_w : i])
            cand_pool = set()
            for l in lags:
                if i - l >= 0:
                    cand_pool.add(nums[i - l])

            cands = sorted(list((cand_pool - rec_set) - blacklist))

            if actual in rec_set and actual in cands:
                leak_count += 1

            skip_anti_cluster = (use_anti_cluster and prev_was_repeat)

            # Canal A: Disparo de Canasta por Lags Armónicos
            if cands and not skip_anti_cluster:
                hit = (actual in cands)
                if streak in target_streaks:
                    events.append({
                        "dt": dts[i],
                        "fecha": d,
                        "hora": df.iloc[i]["hora"],
                        "ruleta": r_name,
                        "channel": "Lag_Basket",
                        "cost_units": len(cands),
                        "cands": cands,
                        "actual": actual,
                        "hit": hit,
                        "payout": payout,
                        "f_unit": f_unit,
                        "trigger_misses": trigger_misses
                    })
                    if hit:
                        trigger_misses = 0
                    else:
                        trigger_misses += 1
                streak = 0 if hit else streak + 1
            elif cands and skip_anti_cluster:
                hit = (actual in cands)
                streak = 0 if hit else streak + 1
                if streak in target_streaks:
                    trigger_misses += 1

            # Canal B: Disparo Markov Sniper Mono-Animal (1 sola ficha a cuota 30x/60x)
            markov_target = markov_snipers.get(prev_num)
            if markov_target and markov_target not in rec_set and markov_target not in blacklist:
                # Se dispara únicamente a ese único animal
                m_hit = (actual == markov_target)
                events.append({
                    "dt": dts[i],
                    "fecha": d,
                    "hora": df.iloc[i]["hora"],
                    "ruleta": r_name,
                    "channel": "Markov_Sniper",
                    "cost_units": 1,  # 1 sola ficha
                    "cands": [markov_target],
                    "actual": actual,
                    "hit": m_hit,
                    "payout": payout,
                    "f_unit": f_unit * 0.75,  # 75% del f_unit estándar
                    "trigger_misses": 1
                })

            is_repeat_now = (actual in seen_today)
            seen_today.add(actual)
            prev_was_repeat = is_repeat_now

    events.sort(key=lambda x: x["dt"])
    return events, leak_count


def simulate_portfolio(events, initial_bankroll=200.0, base_kelly=0.75, target_mdd=0.32, cb_limit=0.15, decay_weeks=12, min_bet=0.10):
    if not events:
        return None

    start_dt = events[0]["dt"]
    for ev in events:
        ev["week_idx"] = int((ev["dt"] - start_dt).total_seconds() // (7 * 86400))

    total_weeks = events[-1]["week_idx"] + 1
    weeks_dict = {w: [] for w in range(total_weeks)}
    for ev in events:
        weeks_dict[ev["week_idx"]].append(ev)

    b = initial_bankroll
    peak = b
    max_mdd = 0.0
    total_invested = 0.0
    total_collected = 0.0
    gross_profits = 0.0
    gross_losses = 0.0
    total_bets = 0
    total_wins = 0

    weekly_pnl = []
    weekly_returns = []
    equity_curve = [b]
    roulette_stats = defaultdict(lambda: {"bets": 0, "wins": 0, "invested": 0.0, "collected": 0.0})

    decay_factor = 0.5 ** (1.0 / decay_weeks) if decay_weeks > 0 else 1.0

    for w in range(total_weeks):
        evs = weeks_dict[w]
        b_start = b

        peak = max(b_start, peak * decay_factor)
        curr_dd = (peak - b_start) / peak if peak > 0 else 0.0
        damping = max(0.15, 1.0 - (curr_dd / target_mdd))
        eff_kelly = base_kelly * damping

        weekly_stakes = {
            ev["ruleta"]: max(min_bet, round(b_start * ev["f_unit"] * eff_kelly, 2))
            for ev in evs
        }

        pnl_w = 0.0
        cb_tripped = False

        for ev in evs:
            if cb_limit > 0 and pnl_w <= -b_start * cb_limit:
                cb_tripped = True
                break

            base_stk = weekly_stakes[ev["ruleta"]]
            t_miss = ev["trigger_misses"]

            if ev["channel"] == "Markov_Sniper":
                smart_mult = 1.20  # Boost por hiper-probabilidad markoviana
            else:
                smart_mult = 1.25 if (1 <= t_miss <= 3) else (0.85 if t_miss == 0 else 1.00)

            stk_unit = max(min_bet, round(base_stk * smart_mult, 2))
            bet_cost = round(stk_unit * ev["cost_units"], 2)

            if bet_cost > b:
                if b >= ev["cost_units"] * min_bet:
                    stk_unit = min_bet
                    bet_cost = round(stk_unit * ev["cost_units"], 2)
                else:
                    b = 0.0
                    break

            total_invested += bet_cost
            total_bets += 1

            r_st = roulette_stats[ev["ruleta"]]
            r_st["bets"] += 1
            r_st["invested"] += bet_cost

            if ev["hit"]:
                cob = round(stk_unit * ev["payout"], 2)
                pnl = round(cob - bet_cost, 2)
                gross_profits += pnl
                total_wins += 1
                r_st["wins"] += 1
            else:
                cob = 0.0
                pnl = -bet_cost
                gross_losses += bet_cost

            total_collected += cob
            r_st["collected"] += cob
            pnl_w += pnl
            b = round(b + pnl, 2)

            equity_curve.append(b)
            if b > peak:
                peak = b
            dd = (peak - b) / peak if peak > 0 else 0.0
            if dd > max_mdd:
                max_mdd = dd

        weekly_pnl.append(pnl_w)
        w_ret = (pnl_w / b_start) if b_start > 0 else 0.0
        weekly_returns.append(w_ret)

        if b <= 10.0:
            break

    win_rate = (total_wins / total_bets * 100.0) if total_bets > 0 else 0.0
    profit_factor = (gross_profits / gross_losses) if gross_losses > 0 else float("inf")
    net_pnl = total_collected - total_invested
    roi = (net_pnl / total_invested * 100.0) if total_invested > 0 else 0.0
    expectancy_per_bet = (net_pnl / total_bets) if total_bets > 0 else 0.0

    r_arr = np.array(weekly_returns)
    mean_w = np.mean(r_arr) if len(r_arr) > 0 else 0.0
    std_w = np.std(r_arr, ddof=1) if len(r_arr) > 1 else 0.0
    sharpe = (mean_w / std_w * math.sqrt(52)) if std_w > 0 else 0.0

    downside = r_arr[r_arr < 0]
    downside_dev = math.sqrt(np.mean(downside ** 2)) if len(downside) > 0 else 0.0
    sortino = (mean_w / downside_dev * math.sqrt(52)) if downside_dev > 0 else float("inf")

    n_weeks = len(weekly_returns)
    cagr_weekly = ((b / initial_bankroll) ** (1.0 / n_weeks) - 1.0) * 100.0 if (n_weeks > 0 and b > 0) else 0.0

    return {
        "initial_bankroll": initial_bankroll,
        "final_bankroll": b,
        "net_pnl": net_pnl,
        "total_invested": total_invested,
        "total_collected": total_collected,
        "total_bets": total_bets,
        "total_wins": total_wins,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "expectancy_per_bet": expectancy_per_bet,
        "roi": roi,
        "max_drawdown": max_mdd * 100.0,
        "sharpe": sharpe,
        "sortino": sortino,
        "cagr_weekly": cagr_weekly,
        "n_weeks": n_weeks,
        "winning_weeks": sum(1 for p in weekly_pnl if p > 0),
        "roulette_stats": dict(roulette_stats)
    }

if __name__ == "__main__":
    events, leak = extract_parsimonious_events()
    print(f"Total Disparos Generados: {len(events):,} (Leakage: {leak})")
    res = simulate_portfolio(events, initial_bankroll=200.0)

    print("\n" + "=" * 100)
    print("📊 RESULTADOS OFICIALES: SISTEMA PARSIMONIOSO CON SNIPER MARKOVIANO MONO-ANIMAL")
    print("=" * 100)
    print(f"Capital Inicial:            ${res['initial_bankroll']:,.2f} USD")
    print(f"Capital Final Alcanzado:    ${res['final_bankroll']:,.2f} USD")
    print(f"Ganancia Neta (PnL):        +${res['net_pnl']:,.2f} USD (+{((res['final_bankroll']/200.0)-1)*100:,.2f}%)")
    print(f"CAGR Semanal Compuesto:     +{res['cagr_weekly']:.2f}% semanal")
    print(f"Máximo Drawdown Histórico:  {res['max_drawdown']:.2f}%")
    print(f"Total Disparos Ejecutados:  {res['total_bets']:,} bets")
    print(f"Aciertos Totales:           {res['total_wins']:,} ({res['win_rate']:.2f}%)")
    print(f"Profit Factor:              {res['profit_factor']:.2f}")
    print(f"Expectancy por Disparo:     ${res['expectancy_per_bet']:,.2f} USD")
    print(f"ROI sobre Capital Apostado: {res['roi']:.2f}%")
    print(f"Sharpe Ratio Anualizado:    {res['sharpe']:.2f}")
    print(f"Sortino Ratio Anualizado:   {res['sortino']:.2f}")
    print(f"Semanas Ganadoras:          {res['winning_weeks']} de {res['n_weeks']} ({res['winning_weeks']/res['n_weeks']*100:.1f}%)")

    print("\n" + "-" * 100)
    print("🎯 RENDIMIENTO POR RULETA")
    print("-" * 100)
    for r_name, st in res["roulette_stats"].items():
        r_pnl = st["collected"] - st["invested"]
        r_roi = (r_pnl / st["invested"] * 100.0) if st["invested"] > 0 else 0.0
        r_wr = (st["wins"] / st["bets"] * 100.0) if st["bets"] > 0 else 0.0
        print(f"{r_name:<18} | Disparos: {st['bets']:>4} | Aciertos: {st['wins']:>3} ({r_wr:>5.2f}%) | Invertido: ${st['invested']:>11,.2f} | Cobrado: ${st['collected']:>11,.2f} | PnL: {'+' if r_pnl>=0 else ''}${r_pnl:>11,.2f} | ROI: {r_roi:>+6.2f}%")

    with open(r"C:\Users\victo\nuevas_ruletas\scratch\parsimonious_system_results.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
