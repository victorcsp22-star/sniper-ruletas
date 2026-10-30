"""
========================================================================================
 ANÁLISIS CUANTITATIVO PROFUNDO: LOTTO BRASIL Y LOTTO BICHO (SANDBOX AISLADO)
========================================================================================
Módulo 100% aislado del portafolio principal.
Analiza la estructura matemática de las dos ruletas brasileñas:
1. Supresión de lags cortos (L=1..6) y picos de rebote (L >= 7).
2. Probabilidad empírica, Z-scores y p-values vs ruido uniforme.
3. Gatillo Post-Fallo 1 (Sniper) y cálculo de rachas perdedoras máximas.
4. Derivación formal del Criterio de Kelly (payout portal 37x/35x y conservador 30x).
5. Simulación de crecimiento compuesto con $1,000 USD (Full Kelly vs Grossman-Zhou).
6. Comparativa dimensional vs el portafolio de 5 ruletas venezolanas.
========================================================================================
"""

import os
import sys
import numpy as np
import pandas as pd
from scipy import stats

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOTTERIES = {
    "lottobrasil": {
        "name": "Lotto Brasil",
        "csv": os.path.join(BASE_DIR, "lottobrasil_2anios.csv"),
        "k_universe": 38,
        "portal_payout": 37.0,
        "standard_payout": 30.0,
        "emoji": "🇧🇷"
    },
    "lottobicho": {
        "name": "Lotto Bicho",
        "csv": os.path.join(BASE_DIR, "lottobicho_2anios.csv"),
        "k_universe": 38,
        "portal_payout": 35.0,
        "standard_payout": 30.0,
        "emoji": "🐆"
    }
}


def analyze_lags(name: str, nums: list, k_univ: int = 38, max_lag: int = 40):
    total = len(nums)
    p0 = 1.0 / k_univ
    
    lag_records = []
    for lag in range(1, max_lag + 1):
        valid = total - lag
        matches = sum(1 for i in range(lag, total) if nums[i] == nums[i - lag])
        p_raw = matches / valid
        se = np.sqrt(p0 * (1.0 - p0) / valid)
        z_score = (p_raw - p0) / se
        p_val = 2 * (1 - stats.norm.cdf(abs(z_score)))

        # Filtro de recencia de 6 horas
        trials_f = 0
        matches_f = 0
        for i in range(max(25, lag), total):
            cand = nums[i - lag]
            if cand not in set(nums[i-6:i]):
                trials_f += 1
                if nums[i] == cand:
                    matches_f += 1
        p_filt = (matches_f / trials_f) if trials_f > 0 else 0.0

        lag_records.append({
            "lag": lag,
            "matches_raw": matches,
            "trials_raw": valid,
            "pct_raw": p_raw * 100.0,
            "z_score": z_score,
            "p_value": p_val,
            "matches_filt": matches_f,
            "trials_filt": trials_f,
            "pct_filt": p_filt * 100.0
        })

    df_lags = pd.DataFrame(lag_records)
    return df_lags


def find_optimal_basket(df_lags: pd.DataFrame, min_lag: int = 7, basket_sizes=[3, 4, 5]):
    rebound = df_lags[df_lags["lag"] >= min_lag].sort_values(by="pct_filt", ascending=False).reset_index(drop=True)
    return rebound


def run_gatillo_backtest(nums: list, top_lags: list, payout: float, trigger_fallos: int = 1):
    total = len(nums)
    streak = 0
    signals = 0
    hits = 0
    flat_profit = 0.0
    total_cost = 0.0
    losing_streaks = []
    cur_loss_streak = 0

    for i in range(max(top_lags) + 7, total):
        actual = nums[i]
        rec6 = set(nums[i-6:i])
        cands = list({nums[i-l] for l in top_lags} - rec6)
        cost = len(cands)
        hit = (actual in cands)

        # Disparo bajo gatillo
        if streak >= trigger_fallos and cost > 0:
            signals += 1
            total_cost += cost
            if hit:
                hits += 1
                flat_profit += (payout - cost)
                losing_streaks.append(cur_loss_streak)
                cur_loss_streak = 0
            else:
                flat_profit -= cost
                cur_loss_streak += 1

        if hit:
            streak = 0
        else:
            streak += 1

    if cur_loss_streak > 0:
        losing_streaks.append(cur_loss_streak)

    win_rate = (hits / signals * 100.0) if signals > 0 else 0.0
    roi = (flat_profit / total_cost * 100.0) if total_cost > 0 else 0.0
    max_ls = max(losing_streaks) if losing_streaks else 0

    # Kelly derivation
    avg_cost = (total_cost / signals) if signals > 0 else len(top_lags)
    b = (payout / avg_cost) - 1.0
    p = win_rate / 100.0
    q = 1.0 - p
    f_star = max(0.0, (b * p - q) / b) if b > 0 else 0.0
    f_unit = f_star / avg_cost if avg_cost > 0 else 0.0

    return {
        "signals": signals,
        "hits": hits,
        "win_rate": win_rate,
        "flat_profit": flat_profit,
        "roi": roi,
        "avg_basket_cost": avg_cost,
        "max_losing_streak": max_ls,
        "b_odds": b,
        "f_star_basket": f_star,
        "f_unit": f_unit,
        "is_positive_ev": (b * p - q) > 0
    }


def simulate_compounding(nums: list, top_lags: list, payout: float, f_unit: float, initial_bankroll: float = 1000.0, mdd_floor: float = 0.40):
    total = len(nums)
    streak = 0
    
    # Trackers for Full Kelly & Grossman-Zhou
    b_kelly = initial_bankroll
    b_gz = initial_bankroll
    peak_kelly = initial_bankroll
    peak_gz = initial_bankroll
    mdd_kelly = 0.0
    mdd_gz = 0.0

    history_kelly = [initial_bankroll]
    history_gz = [initial_bankroll]

    for i in range(max(top_lags) + 7, total):
        actual = nums[i]
        rec6 = set(nums[i-6:i])
        cands = list({nums[i-l] for l in top_lags} - rec6)
        cost = len(cands)
        hit = (actual in cands)

        if streak >= 1 and cost > 0:
            # Full Kelly stake
            bet_per_cand_k = b_kelly * f_unit
            bet_total_k = bet_per_cand_k * cost

            if hit:
                b_kelly += bet_per_cand_k * payout - bet_total_k
            else:
                b_kelly -= bet_total_k

            if b_kelly > peak_kelly:
                peak_kelly = b_kelly
            dd_k = (peak_kelly - b_kelly) / peak_kelly if peak_kelly > 0 else 0.0
            if dd_k > mdd_kelly:
                mdd_kelly = dd_k
            history_kelly.append(b_kelly)

            # Grossman-Zhou Damped Kelly stake
            floor = peak_gz * (1.0 - mdd_floor)
            cushion = max(0.0, (b_gz - floor) / b_gz) if b_gz > 0 else 0.0
            damping = cushion ** 1.5
            bet_per_cand_gz = b_gz * f_unit * damping
            bet_total_gz = bet_per_cand_gz * cost

            if hit:
                b_gz += bet_per_cand_gz * payout - bet_total_gz
            else:
                b_gz -= bet_total_gz

            if b_gz > peak_gz:
                peak_gz = b_gz
            dd_gz = (peak_gz - b_gz) / peak_gz if peak_gz > 0 else 0.0
            if dd_gz > mdd_gz:
                mdd_gz = dd_gz
            history_gz.append(b_gz)

        if hit:
            streak = 0
        else:
            streak += 1

    return {
        "final_kelly": b_kelly,
        "mdd_kelly": mdd_kelly * 100.0,
        "final_gz": b_gz,
        "mdd_gz": mdd_gz * 100.0,
        "history_kelly": history_kelly,
        "history_gz": history_gz
    }


def run_full_deep_sandbox():
    print("=" * 100)
    print("🔬 ESTUDIO CUANTITATIVO RIGUROSO: LOTTO BRASIL & LOTTO BICHO (ISOLADO)")
    print("=" * 100)

    results = {}

    for k, meta in LOTTERIES.items():
        df = pd.read_csv(meta["csv"])
        nums = df["numero"].astype(str).tolist()
        total_draws = len(nums)
        p0 = 1.0 / meta["k_universe"]
        be_portal = (1.0 / meta["portal_payout"]) * 100.0
        be_std = (1.0 / meta["standard_payout"]) * 100.0

        print(f"\n{'-'*100}")
        print(f" {meta['emoji']} {meta['name'].upper()} | Sorteos: {total_draws:,} | Fechas: {df['fecha'].min()} al {df['fecha'].max()}")
        print(f"   Universo: {meta['k_universe']} números | Payout Portal: {meta['portal_payout']:.0f}x (BE: {be_portal:.2f}%) | Payout Std: {meta['standard_payout']:.0f}x (BE: {be_std:.2f}%)")
        print(f"{'-'*100}")

        # 1. Análisis de Lags
        df_lags = analyze_lags(meta["name"], nums, meta["k_universe"])
        
        # Supresión de Lags Cortos L=1..6
        short_lags = df_lags[df_lags["lag"] <= 6]
        avg_short_raw = short_lags["pct_raw"].mean()
        avg_short_z = short_lags["z_score"].mean()

        print(f">> ANÁLISIS DE SUPRESIÓN EN LAGS CORTOS (Lag 1 al 6):")
        print(f"   • Probabilidad promedio observada: {avg_short_raw:.3f}% vs Azar Puro (1/38): {p0*100:.3f}%")
        print(f"   • Z-Score promedio: {avg_short_z:+.2f} ({'Supresión Fuerte' if avg_short_z < -1.0 else 'Comportamiento Normal'})")
        for _, row in short_lags.iterrows():
            print(f"     - Lag {int(row['lag'])}: {row['pct_raw']:.2f}% | Z: {row['z_score']:+.2f}")

        # Top Lags de Rebote (Lag >= 7)
        rebound = find_optimal_basket(df_lags)
        print(f"\n>> TOP 8 LAGS CON MAYOR EFECTO REBOTE FILTRADO (Lag >= 7):")
        print(f"   {'Lag':<5} | {'Prob Bruta':<12} | {'Prob Filtrada':<15} | {'Z-Score':<10} | {'EV Portal ('+str(meta['portal_payout'])+'x)':<18} | {'EV Std (30x)':<12}")
        print(f"   {'-'*80}")
        for _, row in rebound.head(8).iterrows():
            ev_p = "✅ +EV" if row["pct_filt"] > be_portal else "❌ -EV"
            ev_s = "✅ +EV" if row["pct_filt"] > be_std else "❌ -EV"
            print(f"   Lag {int(row['lag']):<2} | {row['pct_raw']:<12.2f}% | {row['pct_filt']:<15.2f}% | {row['z_score']:<+10.2f} | {ev_p:<18} | {ev_s:<12}")

        # Canastas candidatas
        baskets = {
            "Top 3 Lags": rebound["lag"].head(3).tolist(),
            "Top 4 Lags": rebound["lag"].head(4).tolist(),
            "Top 5 Lags": rebound["lag"].head(5).tolist()
        }

        print(f"\n>> BACKTEST CON GATILLO POST-FALLO 1 (SNIPER VIRTUAL):")
        best_b = None
        best_f_unit = 0
        best_payout = meta["portal_payout"]

        for b_name, b_lags in baskets.items():
            res_portal = run_gatillo_backtest(nums, b_lags, meta["portal_payout"])
            res_std = run_gatillo_backtest(nums, b_lags, meta["standard_payout"])
            print(f"\n   --- {b_name}: Lags {b_lags} ---")
            print(f"   [PORTAL {meta['portal_payout']:.0f}x] Señales: {res_portal['signals']} | Win Rate: {res_portal['win_rate']:.2f}% (BE {be_portal:.2f}%) | ROI: {res_portal['roi']:+.2f}% | Racha Pérdida Máx: {res_portal['max_losing_streak']}")
            print(f"               Kelly Cesta: {res_portal['f_star_basket']*100:.2f}% | Kelly Unitario: {res_portal['f_unit']*100:.3f}% | +EV: {res_portal['is_positive_ev']}")
            print(f"   [STD 30x]    Señales: {res_std['signals']} | Win Rate: {res_std['win_rate']:.2f}% (BE {be_std:.2f}%) | ROI: {res_std['roi']:+.2f}% | Racha Pérdida Máx: {res_std['max_losing_streak']}")
            print(f"               Kelly Cesta: {res_star*100:.2f}%" if (res_star := res_std['f_star_basket']) > 0 else f"               Kelly: 0.00% (-EV)")

            if b_name == "Top 4 Lags":
                best_b = b_lags
                best_f_unit = res_portal["f_unit"]

        # Simulación de Crecimiento Compuesto con $1,000 USD
        print(f"\n>> SIMULACIÓN DE CAPITAL $1,000 USD (Top 4 Lags {best_b} | Payout {meta['portal_payout']}x):")
        sim = simulate_compounding(nums, best_b, meta["portal_payout"], best_f_unit, initial_bankroll=1000.0, mdd_floor=0.40)
        print(f"   • FULL KELLY PURO:")
        print(f"     Balance Final: ${sim['final_kelly']:,.2f} USD")
        print(f"     Max Drawdown:  {sim['mdd_kelly']:.2f}%")
        print(f"   • GROSSMAN-ZHOU (Control MDD Floor 40%):")
        print(f"     Balance Final: ${sim['final_gz']:,.2f} USD")
        print(f"     Max Drawdown:  {sim['mdd_gz']:.2f}%")

        results[k] = {
            "meta": meta,
            "df_lags": df_lags,
            "rebound": rebound,
            "best_lags": best_b,
            "sim": sim,
            "portal_bt": run_gatillo_backtest(nums, best_b, meta["portal_payout"]),
            "std_bt": run_gatillo_backtest(nums, best_b, meta["standard_payout"])
        }

    return results

if __name__ == "__main__":
    run_full_deep_sandbox()
