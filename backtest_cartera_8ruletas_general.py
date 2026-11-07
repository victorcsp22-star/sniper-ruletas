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

def extract_events_portfolio(active_configs):
    all_events = []
    
    hora_rank_map = {
        "08:30 AM": 1, "09:30 AM": 2, "10:30 AM": 3, "11:30 AM": 4,
        "12:30 PM": 5, "01:30 PM": 6, "02:30 PM": 7, "03:30 PM": 8,
        "04:30 PM": 9, "05:30 PM": 10, "06:30 PM": 11, "07:30 PM": 12
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
        min_hour = cfg.get("min_hour", None)
        only_clean_day = cfg.get("only_clean_day", False)
        
        nums = df["numero"].tolist()
        min_idx = max(lags) + 6
        
        streak = 0
        trigger_misses = 0
        seen_today = set()
        day_repeat = False
        cur_date = None
        for i in range(min_idx, len(nums)):
            actual = nums[i]
            d = df.iloc[i]["fecha"]
            h_str = df.iloc[i]["hora"]
            
            if d != cur_date:
                cur_date = d
                seen_today = set()
                day_repeat = False
                
            if actual in seen_today:
                day_repeat = True
                
            rec6 = set(nums[i-6:i])
            
            if only_clean_day:
                cands = list(set([nums[i-l] for l in lags if i >= l]) - rec6 - seen_today)
            else:
                cands = list(set([nums[i-l] for l in lags if i >= l]) - rec6)
                
            operate = True
            if min_hour is not None:
                hr_idx = hora_rank_map.get(h_str, 99)
                if hr_idx < min_hour:
                    operate = False
            if only_clean_day and day_repeat:
                operate = False
                
            # Disparo para ruletas estándar vs ruleta internacional (represión intradía)
            if only_clean_day:
                if cands and operate:
                    # Toma el Top 1 candidato vivo con mayor afinidad
                    scored_cands = [(c, sum(1.0 for l in lags if i >= l and nums[i-l] == c)) for c in cands]
                    scored_cands.sort(key=lambda x: x[1], reverse=True)
                    best_targets = [x[0] for x in scored_cands[:1]]
                    
                    hit = (actual in best_targets)
                    all_events.append({
                        "dt": df.iloc[i]["sort_dt"],
                        "fecha": df.iloc[i]["fecha"],
                        "hora": df.iloc[i]["hora"],
                        "ruleta": r_name,
                        "cost_units": len(best_targets),
                        "hit": hit,
                        "payout": payout,
                        "f_unit": f_unit,
                        "trigger_misses": trigger_misses
                    })
                    trigger_misses = 0 if hit else trigger_misses + 1
            else:
                if cands:
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
                        trigger_misses = 0 if hit else trigger_misses + 1
                    if hit:
                        streak = 0
                    else:
                        streak += 1
                else:
                    streak = 0
                
            seen_today.add(actual)

    all_events.sort(key=lambda x: x["dt"])
    return all_events

def run_portfolio_simulation(all_events, initial_bankroll=200.0, base_kelly=0.75, target_mdd=0.32, cb_limit=0.15, decay_weeks=12, quarantine_misses=20):
    start_dt = all_events[0]["dt"]
    for ev in all_events:
        ev["week_idx"] = int((ev["dt"] - start_dt).total_seconds() // (7 * 86400))

    total_weeks = all_events[-1]["week_idx"] + 1
    weeks_dict = {w: [] for w in range(total_weeks)}
    for ev in all_events:
        weeks_dict[ev["week_idx"]].append(ev)

    b = initial_bankroll
    peak = b
    max_mdd = 0.0
    decay_factor = 0.5 ** (1.0 / decay_weeks) if decay_weeks > 0 else 1.0

    weekly_log = []
    total_bets = 0
    total_wins = 0
    running_pnl = 0.0
    equity_curve = [b]

    for w in range(total_weeks):
        evs = weeks_dict[w]
        b_start = b

        # Desvanecimiento del ATH
        peak = max(b_start, peak * decay_factor)
        curr_dd = (peak - b_start) / peak if peak > 0 else 0.0

        # Amortiguación funcional de Kelly
        damping = max(0.15, 1.0 - (curr_dd / target_mdd)) if target_mdd > 0 else 1.0
        eff_kelly = base_kelly * damping

        # Apuestas fijadas para la semana por ruleta
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
            
            # Smart Investment multiplier
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
        if b > peak:
            peak = b

        ret_w = (pnl_w / b_start) if b_start > 0 else 0.0
        weekly_log.append({
            "week": w + 1,
            "b_start": b_start,
            "b_end": b_end,
            "pnl": pnl_w,
            "ret_pct": ret_w * 100.0,
            "bets": bets_w,
            "wins": wins_w,
            "cb_hit": cb_hit,
            "eff_kelly": eff_kelly,
            "peak": peak,
            "dd_close": (peak - b_end) / peak if peak > 0 else 0.0
        })

    df_w = pd.DataFrame(weekly_log)
    net_growth = round(b - initial_bankroll, 2)
    pos_w = (df_w["pnl"] > 0).sum()
    neg_w = (df_w["pnl"] < 0).sum()
    sharpe = df_w["ret_pct"].mean() / df_w["ret_pct"].std() * np.sqrt(52) if df_w["ret_pct"].std() > 0 else 0.0
    downside_std = df_w[df_w["ret_pct"] < 0]["ret_pct"].std()
    sortino = df_w["ret_pct"].mean() / downside_std * np.sqrt(52) if downside_std > 0 else 0.0

    return {
        "final_bankroll": b,
        "net_growth": net_growth,
        "multiplier": b / initial_bankroll,
        "max_drawdown": max_mdd,
        "total_weeks": total_weeks,
        "pos_weeks": pos_w,
        "neg_weeks": neg_w,
        "sharpe": sharpe,
        "sortino": sortino,
        "df_weeks": df_w,
        "total_bets": total_bets,
        "total_wins": total_wins,
        "win_rate": (total_wins / total_bets * 100.0) if total_bets > 0 else 0,
        "equity_curve": equity_curve
    }

def main():
    print("=" * 115)
    print("🔬 BACKTEST GENERAL DEL SISTEMA: COMPARATIVA CARTERA 7 RULETAS VS CARTERA 8 RULETAS")
    print("   Parámetros Últimos: Step-Compounding 7 Días (0.75x Kelly) | Damping MDD 32% | Peak Decay 12 Semanas")
    print("   Smart Investment Activo (+25% Rebound, -15% Fatigue) | Circuit Breaker 15% | Cuarentena 20 Fallos")
    print("=" * 115)

    # 1. Cartera 7 (Sin Lotto Activo RD)
    cfg_7 = {k: v for k, v in RULETAS_CONFIG.items() if v.get("active", True) and k != "Lotto Activo RD Int"}
    events_7 = extract_events_portfolio(cfg_7)
    res_7_200 = run_portfolio_simulation(events_7, initial_bankroll=200.0)
    res_7_1000 = run_portfolio_simulation(events_7, initial_bankroll=1000.0)

    # 2. Cartera 8 (Con Lotto Activo RD Int)
    cfg_8 = {k: v for k, v in RULETAS_CONFIG.items() if v.get("active", True)}
    events_8 = extract_events_portfolio(cfg_8)
    res_8_200 = run_portfolio_simulation(events_8, initial_bankroll=200.0)
    res_8_1000 = run_portfolio_simulation(events_8, initial_bankroll=1000.0)

    print("\n" + "=" * 115)
    print("RESUMEN COMPARATIVO CON CAPITAL INICIAL DE $200.00 USD:")
    print("=" * 115)
    print(f"CARTERA 7 RULETAS (Previa):")
    print(f"  • Capital Final Auditado     : ${res_7_200['final_bankroll']:>14,.2f} USD ({res_7_200['multiplier']:>8,.1f}x)")
    print(f"  • Ganancia Neta Total        : ${res_7_200['net_growth']:>14,.2f} USD")
    print(f"  • Máximo Drawdown Histórico  : {res_7_200['max_drawdown']*100:>6.2f}%")
    print(f"  • Disparos Totales           : {res_7_200['total_bets']} (Aciertos: {res_7_200['total_wins']}, Tasa: {res_7_200['win_rate']:.2f}%)")
    print(f"  • Semanas Ganadoras          : {res_7_200['pos_weeks']} de {res_7_200['total_weeks']} ({res_7_200['pos_weeks']/res_7_200['total_weeks']*100:.1f}%)")
    print(f"  • Ratio de Sharpe Anualizado : {res_7_200['sharpe']:.2f} | Sortino: {res_7_200['sortino']:.2f}")

    print(f"\nCARTERA 8 RULETAS (+ Lotto Activo RD Internacional):")
    print(f"  • Capital Final Auditado     : ${res_8_200['final_bankroll']:>14,.2f} USD ({res_8_200['multiplier']:>8,.1f}x)")
    print(f"  • Ganancia Neta Total        : ${res_8_200['net_growth']:>14,.2f} USD  (+${res_8_200['net_growth'] - res_7_200['net_growth']:,.2f} USD adicionales)")
    print(f"  • Máximo Drawdown Histórico  : {res_8_200['max_drawdown']*100:>6.2f}%")
    print(f"  • Disparos Totales           : {res_8_200['total_bets']} (Aciertos: {res_8_200['total_wins']}, Tasa: {res_8_200['win_rate']:.2f}%)")
    print(f"  • Semanas Ganadoras          : {res_8_200['pos_weeks']} de {res_8_200['total_weeks']} ({res_8_200['pos_weeks']/res_8_200['total_weeks']*100:.1f}%)")
    print(f"  • Ratio de Sharpe Anualizado : {res_8_200['sharpe']:.2f} | Sortino: {res_8_200['sortino']:.2f}")

    print("\n" + "=" * 115)
    print("RESUMEN COMPARATIVO CON CAPITAL INICIAL DE $1,000.00 USD:")
    print("=" * 115)
    print(f"  • Cartera 7 Ruletas: Final = ${res_7_1000['final_bankroll']:>14,.2f} USD ({res_7_1000['multiplier']:>8,.1f}x) | MDD = {res_7_1000['max_drawdown']*100:.2f}% | Sharpe = {res_7_1000['sharpe']:.2f}")
    print(f"  • Cartera 8 Ruletas: Final = ${res_8_1000['final_bankroll']:>14,.2f} USD ({res_8_1000['multiplier']:>8,.1f}x) | MDD = {res_8_1000['max_drawdown']*100:.2f}% | Sharpe = {res_8_1000['sharpe']:.2f}")

    # Gráfico Institucional
    fig, axes = plt.subplots(2, 1, figsize=(15, 11), gridspec_kw={'height_ratios': [2.2, 1]})
    fig.suptitle("Backtest General del Sistema: Cartera 8 Ruletas (+ Lotto Activo RD Internacional)\nStep-Compounding 7 Días Optimizado | Capital Inicial: $200.00 USD (2 Años Históricos)", fontsize=13, fontweight='bold')

    ax1 = axes[0]
    ax1.plot(res_8_200["equity_curve"], label=f'Cartera 8 Ruletas (Con RD Int): ${res_8_200["final_bankroll"]:,.2f} USD ({res_8_200["multiplier"]:,.1f}x, Sharpe={res_8_200["sharpe"]:.2f})', color='#2ca02c', linewidth=2.2)
    ax1.plot(res_7_200["equity_curve"], label=f'Cartera 7 Ruletas (Sin RD Int): ${res_7_200["final_bankroll"]:,.2f} USD ({res_7_200["multiplier"]:,.1f}x, Sharpe={res_7_200["sharpe"]:.2f})', color='#1f77b4', linewidth=1.8, linestyle='--')
    ax1.axhline(200.0, color='black', linestyle=':', label='Capital Inicial ($200.00 USD)')
    ax1.set_title("Curva de Crecimiento del Sistema ($ USD) - Escala Logarítmica", fontweight='bold')
    ax1.set_ylabel("Capital ($ USD)")
    ax1.set_yscale("log")
    ax1.legend(loc='upper left', fontsize=9.5)
    ax1.grid(True, alpha=0.3, which='both')

    ax2 = axes[1]
    # Drawdown en porcentaje
    arr8 = np.array(res_8_200["equity_curve"])
    pk8 = np.maximum.accumulate(arr8)
    dd8 = (pk8 - arr8) / pk8 * 100.0
    arr7 = np.array(res_7_200["equity_curve"])
    pk7 = np.maximum.accumulate(arr7)
    dd7 = (pk7 - arr7) / pk7 * 100.0

    ax2.plot(dd8, label=f'Cartera 8 Ruletas (Max DD: {res_8_200["max_drawdown"]*100:.2f}%)', color='#2ca02c', linewidth=1.5)
    ax2.plot(dd7, label=f'Cartera 7 Ruletas (Max DD: {res_7_200["max_drawdown"]*100:.2f}%)', color='#1f77b4', linewidth=1.2, linestyle='--')
    ax2.axhline(32.0, color='red', linestyle=':', label='Drawdown Objetivo Teórico (32.0%)')
    ax2.set_title("Evolución del Drawdown Intradía (%)", fontweight='bold')
    ax2.set_xlabel("Número de Eventos de Disparo")
    ax2.set_ylabel("Drawdown (%)")
    ax2.legend(loc='upper right', fontsize=9)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    chart_path = os.path.join(OUTPUT_DIR, "grafica_backtest_general_cartera_8ruletas.png")
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"\nGráfica institucional guardada en: {chart_path}")

if __name__ == "__main__":
    main()
