"""
========================================================================================
 COMPARADOR MAESTRO DE BACKTEST INSTITUCIONAL (BASE vs MEJORADO POR ANOMALÍAS)
========================================================================================
Compara la Cartera Oficial (7 Ruletas) bajo dos configuraciones:
 1. Cartera Base Actual: Filtro rec_6 homogéneo.
 2. Cartera Mejorada (Tailored Dynamic):
    - Lotto Activo: rec_6 + Filtro Anti-Clustering (evita disparo post-repetición).
    - Ruleta Royal: rec_6 + Filtro Anti-Clustering.
    - La Granjita: rec_8 (purga profunda de cola corta, ROI +33.9% vs +19.6%).
    - Mega Animal 40: rec_8 (purga profunda, ROI +38.6% vs +27.4%).
    - Guácharo Activo: rec_8 (ROI +44.9% vs +40.7%).
    - Gatazo y Monje: rec_6 (estelar estándar).

Ejecuta simulación con interés compuesto semanal ($200 USD inicial), Kelly fraccional 0.75x,
amortiguador de drawdown (TARGET_MDD = 32%) y disyuntor semanal (-15%).
========================================================================================
"""

import os
import sys
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(r"C:\Users\victo\nuevas_ruletas")
from config import (
    RULETAS_CONFIG, MIN_BET,
    TARGET_MDD, WEEKLY_CIRCUIT_BREAKER_PCT, PEAK_DECAY_WEEKS,
    QUARANTINE_MISSES, WEEKLY_KELLY_MULTIPLIER,
    SMART_INVESTMENT_ENABLED, REBOUND_BOOST_MULTIPLIER,
    FATIGUE_DISCOUNT_MULTIPLIER, NEUTRAL_MULTIPLIER
)

OUTPUT_DIR = r"C:\Users\victo\.gemini\antigravity\brain\da61199f-f45d-4b1d-bcd9-a17212f844b0"

def extract_portfolio_events(active_configs, mode="base"):
    all_events = []
    
    # Specific per-roulette tuning under 'enhanced' mode
    enhanced_tuning = {
        "Lotto Activo": {"rec_w": 6, "anti_cluster": True},
        "Ruleta Royal": {"rec_w": 6, "anti_cluster": True},
        "La Granjita": {"rec_w": 8, "anti_cluster": False},
        "Mega Animal 40": {"rec_w": 8, "anti_cluster": False},
        "Guacharo Activo": {"rec_w": 8, "anti_cluster": False},
        "Gatazo": {"rec_w": 6, "anti_cluster": False},
        "Monje Millonario": {"rec_w": 6, "anti_cluster": False},
    }

    for r_name, cfg in active_configs.items():
        if not os.path.exists(cfg["file"]):
            continue
        df = pd.read_csv(cfg["file"], dtype={"numero": str})
        df["numero"] = df["numero"].astype(str).str.strip()
        df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        df = df.sort_values(by="sort_dt").reset_index(drop=True)

        lags = cfg["lags"]
        payout = cfg["payout"]
        f_unit = cfg["f_unit"]
        target_streaks = cfg.get("target_streaks", [1])
        
        nums = df["numero"].tolist()
        dates = df["fecha"].tolist()
        
        if mode == "enhanced":
            tune = enhanced_tuning.get(r_name, {"rec_w": 6, "anti_cluster": False})
            rec_w = tune["rec_w"]
            use_anti_cluster = tune["anti_cluster"]
        else:
            rec_w = 6
            use_anti_cluster = False

        min_idx = max(lags) + max(rec_w, 8)
        
        streak = 0
        trigger_misses = 0
        seen_today = set()
        prev_date = None
        prev_was_repeat = False

        for i in range(min_idx, len(nums)):
            actual = nums[i]
            d = dates[i]
            if d != prev_date:
                prev_date = d
                seen_today = set()
                prev_was_repeat = False

            rec_set = set(nums[i-rec_w:i])
            cands = list(set([nums[i-l] for l in lags if i >= l]) - rec_set)

            is_repeat_now = (actual in seen_today)
            
            skip_shot = False
            if use_anti_cluster and prev_was_repeat:
                skip_shot = True

            if cands and not skip_shot:
                hit = (actual in cands)
                if streak in target_streaks:
                    all_events.append({
                        "dt": df.iloc[i]["sort_dt"],
                        "fecha": df.iloc[i]["fecha"],
                        "hora": df.iloc[i]["hora"],
                        "ruleta": r_name,
                        "cost_units": len(cands),
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
            elif cands and skip_shot:
                hit = (actual in cands)
                streak = 0 if hit else streak + 1
                if streak in target_streaks:
                    # Incurred trigger miss
                    trigger_misses += 1

            seen_today.add(actual)
            prev_was_repeat = is_repeat_now

    all_events.sort(key=lambda x: x["dt"])
    return all_events


def simulate_step_compounding(events, initial_bankroll=200.0, name="Sistema"):
    if not events:
        return {}

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
    total_bets = 0
    total_wins = 0
    running_pnl = 0.0

    decay_factor = 2 ** (-1.0 / PEAK_DECAY_WEEKS)
    cb_limit = WEEKLY_CIRCUIT_BREAKER_PCT
    base_kelly = WEEKLY_KELLY_MULTIPLIER
    target_mdd = TARGET_MDD
    quarantine_misses = QUARANTINE_MISSES

    equity_curve = [b]
    weekly_records = []

    for w in range(total_weeks):
        evs = weeks_dict[w]
        b_start = b

        peak = max(b_start, peak * decay_factor)
        curr_dd = (peak - b_start) / peak if peak > 0 else 0.0

        damping = max(0.15, 1.0 - (curr_dd / target_mdd)) if target_mdd > 0 else 1.0
        eff_kelly = base_kelly * damping

        weekly_stakes = {}
        for ev in evs:
            r = ev["ruleta"]
            if r not in weekly_stakes:
                weekly_stakes[r] = max(MIN_BET, round(b_start * ev["f_unit"] * eff_kelly, 2))

        pnl_w = 0.0
        wins_w = 0
        bets_w = 0
        cb_hit = False

        for ev in evs:
            if cb_limit > 0 and pnl_w <= -b_start * cb_limit:
                cb_hit = True
                break

            if quarantine_misses > 0 and ev["trigger_misses"] >= quarantine_misses:
                continue

            stk = weekly_stakes[ev["ruleta"]]
            
            t_miss = ev["trigger_misses"]
            if SMART_INVESTMENT_ENABLED:
                if t_miss in [1, 2, 3]:
                    mult = REBOUND_BOOST_MULTIPLIER
                elif t_miss == 0:
                    mult = FATIGUE_DISCOUNT_MULTIPLIER
                else:
                    mult = NEUTRAL_MULTIPLIER
            else:
                mult = 1.0

            stk_final = max(MIN_BET, round(stk * mult, 2))
            cost = round(stk_final * ev["cost_units"], 2)
            cob = round(stk_final * ev["payout"], 2) if ev["hit"] else 0.0
            pnl = round(cob - cost, 2)

            pnl_w += pnl
            running_pnl += pnl
            bets_w += 1
            total_bets += 1

            if ev["hit"]:
                wins_w += 1
                total_wins += 1

            intra_b = b_start + pnl_w
            equity_curve.append(intra_b)
            if intra_b > peak:
                peak = intra_b
            dd = (peak - intra_b) / peak if peak > 0 else 0.0
            if dd > max_mdd:
                max_mdd = dd

        b_end = round(max(10.0, b_start + pnl_w), 2)
        b = b_end

        ret_w = (pnl_w / b_start * 100.0) if b_start > 0 else 0.0
        weekly_records.append({
            "week": w + 1,
            "b_start": b_start,
            "b_end": b_end,
            "pnl": pnl_w,
            "return_pct": ret_w,
            "bets": bets_w,
            "wins": wins_w,
            "cb_hit": cb_hit
        })

    tot_return_pct = ((b - initial_bankroll) / initial_bankroll * 100.0)
    win_rate = (total_wins / total_bets * 100.0) if total_bets > 0 else 0.0
    
    # Weekly returns for Sharpe/Sortino
    returns_series = [r["return_pct"] / 100.0 for r in weekly_records]
    mean_ret = np.mean(returns_series) if returns_series else 0.0
    std_ret = np.std(returns_series) if len(returns_series) > 1 else 1e-6
    sharpe = (mean_ret / std_ret * np.sqrt(52)) if std_ret > 0 else 0.0
    
    downside = [r for r in returns_series if r < 0]
    downside_std = np.std(downside) if len(downside) > 1 else 1e-6
    sortino = (mean_ret / downside_std * np.sqrt(52)) if downside_std > 0 else 0.0

    return {
        "name": name,
        "initial_b": initial_bankroll,
        "final_b": b,
        "net_profit": round(b - initial_bankroll, 2),
        "return_pct": tot_return_pct,
        "max_drawdown": max_mdd * 100.0,
        "total_bets": total_bets,
        "total_wins": total_wins,
        "win_rate": win_rate,
        "sharpe": sharpe,
        "sortino": sortino,
        "equity_curve": equity_curve,
        "weekly_records": weekly_records
    }


def main():
    print("=" * 115)
    print("🔬 COMPARATIVA EXPERIMENTAL DE BACKTEST: CARTERA BASE vs CARTERA MEJORADA")
    print("=" * 115)

    active_configs = {k: v for k, v in RULETAS_CONFIG.items() if v.get("active", True)}

    # 1. Simulación Base Oficial
    events_base = extract_portfolio_events(active_configs, mode="base")
    res_base = simulate_step_compounding(events_base, initial_bankroll=200.0, name="Base Oficial (rec_6)")

    # 2. Simulación Mejorada (Tailored Dynamic)
    events_enh = extract_portfolio_events(active_configs, mode="enhanced")
    res_enh = simulate_step_compounding(events_enh, initial_bankroll=200.0, name="Mejorada (rec_8 + Anti-Clustering)")

    print(f"\n{'Métrica Cuantitativa':35s} | {'Base Oficial (Actual)':25s} | {'Cartera Mejorada':25s} | {'Diferencia Relativa':20s}")
    print("-" * 115)
    print(f"{'Capital Inicial':35s} | ${res_base['initial_b']:,.2f} USD{'':11s} | ${res_enh['initial_b']:,.2f} USD{'':11s} | 0.0%")
    print(f"{'Capital Final Acumulado':35s} | ${res_base['final_b']:,.2f} USD{'':9s} | ${res_enh['final_b']:,.2f} USD{'':9s} | {((res_enh['final_b']-res_base['final_b'])/res_base['final_b']*100):+.2f}%")
    print(f"{'Beneficio Neto (PnL)':35s} | ${res_base['net_profit']:,.2f} USD{'':9s} | ${res_enh['net_profit']:,.2f} USD{'':9s} | {((res_enh['net_profit']-res_base['net_profit'])/res_base['net_profit']*100):+.2f}%")
    print(f"{'Rendimiento Total (ROI)':35s} | {res_base['return_pct']:+,.2f}%{'':14s} | {res_enh['return_pct']:+,.2f}%{'':14s} | {(res_enh['return_pct']-res_base['return_pct']):+.2f} pts")
    print(f"{'Max Drawdown Histórico':35s} | {res_base['max_drawdown']:.2f}%{'':19s} | {res_enh['max_drawdown']:.2f}%{'':19s} | {(res_enh['max_drawdown']-res_base['max_drawdown']):+.2f} pts")
    print(f"{'Total Disparos Ejecutados':35s} | {res_base['total_bets']:,} disparos{'':10s} | {res_enh['total_bets']:,} disparos{'':10s} | {res_enh['total_bets']-res_base['total_bets']:+d} disparos")
    print(f"{'Tasa de Acierto (Win Rate)':35s} | {res_base['win_rate']:.2f}%{'':19s} | {res_enh['win_rate']:.2f}%{'':19s} | {(res_enh['win_rate']-res_base['win_rate']):+.2f} pts")
    print(f"{'Sharpe Ratio Anualizado':35s} | {res_base['sharpe']:.2f}{'':21s} | {res_enh['sharpe']:.2f}{'':21s} | {(res_enh['sharpe']-res_base['sharpe']):+.2f}")
    print(f"{'Sortino Ratio Anualizado':35s} | {res_base['sortino']:.2f}{'':20s} | {res_enh['sortino']:.2f}{'':20s} | {(res_enh['sortino']-res_base['sortino']):+.2f}")
    print("=" * 115)

    # 3. Generación del Gráfico Comparativo
    plt.figure(figsize=(14, 7), dpi=300)
    plt.plot(res_base["equity_curve"], label=f"Base Oficial (rec_6) -> ${res_base['final_b']:,.2f} USD (MDD: {res_base['max_drawdown']:.1f}%)", color="#2563EB", linewidth=2.0)
    plt.plot(res_enh["equity_curve"], label=f"Cartera Mejorada (rec_8 + Anti-Clustering) -> ${res_enh['final_b']:,.2f} USD (MDD: {res_enh['max_drawdown']:.1f}%)", color="#059669", linewidth=2.2)

    plt.axhline(200.0, color="#94A3B8", linestyle="--", alpha=0.7, label="Capital Inicial ($200 USD)")
    plt.title("BACKTEST COMPARATIVO: CARTERA OFICIAL BASE vs CARTERA MEJORADA POR ANOMALÍAS\n(Step-Compounding 7 Días | 0.75x Kelly | Target MDD 32% | $200 USD)", fontsize=13, fontweight="bold", pad=15)
    plt.xlabel("Secuencia Cronológica de Disparos Tácticos", fontsize=11)
    plt.ylabel("Patrimonio de Cartera (USD)", fontsize=11)
    plt.yscale("log")
    plt.grid(True, which="both", linestyle=":", alpha=0.5)
    plt.legend(loc="upper left", frameon=True, facecolor="#F8FAFC", edgecolor="#CBD5E1", fontsize=10)
    plt.tight_layout()

    chart_path = os.path.join(OUTPUT_DIR, "grafica_comparativa_base_vs_mejorada_anomalias.png")
    plt.savefig(chart_path)
    plt.close()
    print(f" Gráfica guardada exitosamente en: {chart_path}")

if __name__ == "__main__":
    main()
