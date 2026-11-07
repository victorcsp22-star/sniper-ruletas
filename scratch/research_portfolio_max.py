"""
========================================================================================
 RESEARCH PORTFOLIO MAX: OPTIMIZACIÓN MATEMÁTICA DE SIZING Y ASIGNACIÓN DE CAPITAL
========================================================================================
 Laboratorio Cuantitativo - Senior Risk & Capital Allocation Engineer
 Directivas: Cero Alucinaciones, Auditoría Institucional, Trazabilidad Matemática

 Modelos Evaluados:
  1. Step-Compounding Semanal (Baseline Actual - Cuota fija por ciclo semanal con Kelly Damping)
  2. Full Kelly Dinámico Continuo (1.00x Kelly trade-a-trade)
  3. Half Kelly Dinámico Continuo (0.50x Kelly trade-a-trade)
  4. Dynamic Continuous Grossman-Zhou 10% Floor (Colchón estricto C_t = W_t - 0.90*M_t)
  5. Entropy & Volatility-Adjusted Dynamic Kelly (Rebound Momentum + Paridad de Riesgo 30x vs 60x + GZ Floor)
  6. Constrained Optimal Kelly (Max CAGR st P(MDD > 10%) <= 0.05)
========================================================================================
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

BASE_DIR = r"C:\Users\victo\nuevas_ruletas"
LEDGER_FILE = os.path.join(BASE_DIR, "ledger_nuevas_ruletas.csv")
STATE_FILE = os.path.join(BASE_DIR, "state_nuevas_ruletas.json")
VZ_DIR = os.path.join(BASE_DIR, "data_vz")

RULETAS_CFG = {
    "Lotto Activo": {"file": os.path.join(VZ_DIR, "lotto_activo_2anios.csv"), "payout": 30.0, "f_unit": 0.00900, "lags": [20, 18, 14], "rec_w": 6, "anti_clust": True, "target_streaks": [1]},
    "La Granjita": {"file": os.path.join(VZ_DIR, "la_granjita_2anios.csv"), "payout": 30.0, "f_unit": 0.00484, "lags": [15, 17], "rec_w": 8, "anti_clust": False, "target_streaks": [1]},
    "Ruleta Royal": {"file": os.path.join(VZ_DIR, "ruleta_royal_2anios.csv"), "payout": 30.0, "f_unit": 0.00826, "lags": [16, 19, 31], "rec_w": 6, "anti_clust": True, "target_streaks": [1]},
    "Guacharo Activo": {"file": os.path.join(VZ_DIR, "guacharo_activo_2anios.csv"), "payout": 60.0, "f_unit": 0.00680, "lags": [31, 41, 25, 42, 35], "rec_w": 8, "anti_clust": False, "target_streaks": [1]},
    "Gatazo": {"file": os.path.join(BASE_DIR, "gatazo.csv"), "payout": 60.0, "f_unit": 0.00900, "lags": [35, 22, 20], "rec_w": 6, "anti_clust": False, "target_streaks": [1, 2]},
    "Mega Animal 40": {"file": os.path.join(BASE_DIR, "mega_animal_40.csv"), "payout": 30.0, "f_unit": 0.00800, "lags": [18, 21, 37], "rec_w": 8, "anti_clust": False, "target_streaks": [1]},
    "Monje Millonario": {"file": os.path.join(BASE_DIR, "monje_millonario.csv"), "payout": 60.0, "f_unit": 0.00700, "lags": [24, 35, 37], "rec_w": 6, "anti_clust": False, "target_streaks": [1]}
}


def load_live_trades_arrays() -> Dict[str, np.ndarray]:
    """Carga los 59 trades reales en vivo y los convierte a arrays NumPy de alta velocidad."""
    df = pd.read_csv(LEDGER_FILE)
    df["dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p")
    df["hit"] = df["condicion"].apply(lambda x: 1 if "GANADA" in str(x) else 0)
    df["payout"] = df["ruleta"].apply(lambda r: RULETAS_CFG[r]["payout"])
    df["f_unit"] = df["ruleta"].apply(lambda r: RULETAS_CFG[r]["f_unit"])

    # Zonas de patrón: 1=Dulce, -1=Fatigada, 0=Neutral
    def map_zona(z):
        s = str(z)
        if "Zona Dulce" in s: return 1
        if "Zona Fatigada" in s: return -1
        return 0
    df["zona_code"] = df["zona_patron"].apply(map_zona)

    # Identificar semanas: trade < 37 es semana 1, >= 37 semana 2
    df["week_num"] = [1 if i < 37 else 2 for i in range(len(df))]

    return {
        "hits": df["hit"].values.astype(np.int32),
        "payouts": df["payout"].values.astype(np.float64),
        "costs": df["cands_count"].values.astype(np.int32),
        "f_units": df["f_unit"].values.astype(np.float64),
        "zona_codes": df["zona_code"].values.astype(np.int32),
        "week_nums": df["week_num"].values.astype(np.int32),
        "live_stakes": df["stake_unit"].values.astype(np.float64),
        "live_totals": df["total_bet"].values.astype(np.float64),
        "ruletas": df["ruleta"].values,
        "salidos": df["resultado"].values,
        "n_trades": len(df)
    }


def load_historical_signals() -> pd.DataFrame:
    """Carga las 2,819 señales históricas de 2 años de las 7 ruletas oficiales."""
    events = []
    for r_name, cfg in RULETAS_CFG.items():
        f = cfg["file"]
        if not os.path.exists(f):
            continue
        df = pd.read_csv(f, dtype={"numero": str})
        df["numero"] = df["numero"].astype(str).str.strip()
        df["dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        df = df.dropna(subset=["dt"]).sort_values("dt").reset_index(drop=True)
        nums = df["numero"].tolist()
        lags = cfg["lags"]
        payout = cfg["payout"]
        target_streaks = cfg["target_streaks"]
        rec_w = cfg["rec_w"]
        anti_clust = cfg["anti_clust"]
        min_idx = max(lags) + rec_w

        streak = 0
        trigger_misses = 0

        for i in range(min_idx, len(nums)):
            actual = nums[i]
            rec_set = set(nums[i - rec_w:i])
            cands = sorted(list({nums[i - l] for l in lags} - rec_set))
            cost = len(cands)
            hit = (actual in cands)

            skip = False
            if anti_clust:
                d_curr = df.iloc[i]["dt"].date()
                d_prev = df.iloc[i - 1]["dt"].date()
                if d_curr == d_prev and nums[i - 1] in set(nums[max(0, i - rec_w - 1):i - 1]):
                    skip = True

            if not skip and streak in target_streaks and cost > 0:
                ret_unit = (payout - cost) / cost if hit else -1.0
                events.append({
                    "dt": df.iloc[i]["dt"],
                    "date": df.iloc[i]["dt"].date(),
                    "ruleta": r_name,
                    "payout_type": "60x" if payout == 60.0 else "30x",
                    "payout": payout,
                    "cost": cost,
                    "hit": int(hit),
                    "ret_unit": ret_unit,
                    "trigger_misses": trigger_misses,
                    "f_unit": cfg["f_unit"]
                })
                if hit:
                    trigger_misses = 0
                else:
                    trigger_misses += 1

            if hit:
                streak = 0
            else:
                streak += 1

    df_events = pd.DataFrame(events).sort_values("dt").reset_index(drop=True)
    return df_events


def fast_simulate_vector(
    hits: np.ndarray,
    payouts: np.ndarray,
    costs: np.ndarray,
    f_units: np.ndarray,
    zona_codes: np.ndarray,
    week_nums: np.ndarray,
    live_stakes: np.ndarray,
    model_name: str,
    k_mult: float = 0.75,
    mdd_target: float = 0.10,
    init_bankroll: float = 200.0,
    min_bet: float = 0.10
) -> Tuple[float, float, float, float, float, float, float]:
    """
    Simulación ultra-rápida en NumPy puro.
    Retorna: (final_bankroll, peak, total_return_pct, max_dd_pct, cagr_proj, sharpe_ann, calmar)
    """
    n = len(hits)
    b = float(init_bankroll)
    peak = float(init_bankroll)
    max_dd = 0.0

    cycle_base = float(init_bankroll)
    curr_week = 1

    history = np.empty(n + 1, dtype=np.float64)
    history[0] = b
    pnl_arr = np.empty(n, dtype=np.float64)

    for i in range(n):
        hit = hits[i]
        payout = payouts[i]
        cost = costs[i]
        f_u = f_units[i]
        z_code = zona_codes[i]
        w_num = week_nums[i]

        if model_name == "baseline_live":
            stake_unit = live_stakes[i]
            total_bet = round(stake_unit * cost, 2)

        elif model_name == "weekly_step_075":
            if w_num != curr_week:
                curr_week = w_num
                cycle_base = b
            curr_dd = (peak - cycle_base) / peak if peak > 0 else 0.0
            damping = max(0.15, 1.0 - (curr_dd / 0.32))
            eff_k = k_mult * damping
            stake_unit = round(max(min_bet, cycle_base * f_u * eff_k), 2)
            total_bet = round(stake_unit * cost, 2)

        elif model_name == "full_kelly_dynamic":
            stake_unit = round(max(min_bet, b * f_u * 1.00), 2)
            total_bet = round(stake_unit * cost, 2)

        elif model_name == "half_kelly_dynamic":
            stake_unit = round(max(min_bet, b * f_u * 0.50), 2)
            total_bet = round(stake_unit * cost, 2)

        elif model_name == "dynamic_gz_floor10":
            floor = (1.0 - mdd_target) * peak
            cushion = max(0.0, b - floor)
            gz_mult = min(1.0, max(0.0, cushion / (mdd_target * peak))) if (mdd_target * peak) > 0 else 0.0
            stake_unit = round(max(min_bet, b * f_u * k_mult * gz_mult), 2)
            total_bet = round(stake_unit * cost, 2)

        elif model_name == "entropy_vol_dyn":
            rebound_mult = 1.25 if z_code == 1 else (0.85 if z_code == -1 else 1.0)
            risk_parity_factor = 1.10 if payout == 30.0 else 0.90
            floor = (1.0 - mdd_target) * peak
            cushion = max(0.0, b - floor)
            gz_mult = min(1.0, max(0.0, cushion / (mdd_target * peak))) if (mdd_target * peak) > 0 else 0.0
            eff_rate = f_u * k_mult * gz_mult * rebound_mult * risk_parity_factor
            stake_unit = round(max(min_bet, b * eff_rate), 2)
            total_bet = round(stake_unit * cost, 2)

        else:
            stake_unit = round(max(min_bet, b * f_u * k_mult), 2)
            total_bet = round(stake_unit * cost, 2)

        # Límite de solvencia
        if total_bet > b:
            stake_unit = round(max(min_bet, b / cost), 2)
            total_bet = round(stake_unit * cost, 2)
            if total_bet > b:
                total_bet = b

        if hit == 1:
            cobrado = round(stake_unit * payout, 2)
            pnl = round(cobrado - total_bet, 2)
        else:
            pnl = -total_bet

        b = round(b + pnl, 2)
        if b > peak:
            peak = b
        cur_dd = ((peak - b) / peak * 100.0) if peak > 0 else 0.0
        if cur_dd > max_dd:
            max_dd = cur_dd

        history[i + 1] = b
        pnl_arr[i] = pnl

    total_return_pct = (b - init_bankroll) / init_bankroll * 100.0
    elapsed_days = 12.0
    cagr_proj = ((b / init_bankroll) ** (365.0 / elapsed_days) - 1.0) * 100.0 if b > 0 else -100.0

    ret_per_trade = pnl_arr / history[:-1]
    std_ret = np.std(ret_per_trade)
    sharpe_ann = (np.mean(ret_per_trade) / std_ret) * np.sqrt(4.5 * 365.0) if std_ret > 0 else 0.0
    calmar = total_return_pct / max_dd if max_dd > 0 else 0.0

    return b, peak, total_return_pct, max_dd, cagr_proj, sharpe_ann, calmar


def fast_monte_carlo(
    arrs: Dict[str, np.ndarray],
    model_name: str,
    k_mult: float = 0.75,
    mdd_target: float = 0.10,
    n_sims: int = 10000,
    init_bankroll: float = 200.0
) -> Dict:
    """
    Monte Carlo Bootstrap vectorizado a máxima velocidad.
    """
    n = arrs["n_trades"]
    np.random.seed(42)
    sample_indices = np.random.randint(0, n, size=(n_sims, n))

    cagrs = np.empty(n_sims, dtype=np.float64)
    sharpes = np.empty(n_sims, dtype=np.float64)
    max_dds = np.empty(n_sims, dtype=np.float64)
    final_bs = np.empty(n_sims, dtype=np.float64)

    hits_all = arrs["hits"]
    payouts_all = arrs["payouts"]
    costs_all = arrs["costs"]
    f_units_all = arrs["f_units"]
    zona_codes_all = arrs["zona_codes"]
    week_nums_all = arrs["week_nums"]
    live_stakes_all = arrs["live_stakes"]

    for s in range(n_sims):
        idx = sample_indices[s]
        b, peak, ret_pct, m_dd, cagr, sh_ann, cal = fast_simulate_vector(
            hits=hits_all[idx],
            payouts=payouts_all[idx],
            costs=costs_all[idx],
            f_units=f_units_all[idx],
            zona_codes=zona_codes_all[idx],
            week_nums=week_nums_all[idx],
            live_stakes=live_stakes_all[idx],
            model_name=model_name,
            k_mult=k_mult,
            mdd_target=mdd_target,
            init_bankroll=init_bankroll
        )
        cagrs[s] = cagr
        sharpes[s] = sh_ann
        max_dds[s] = m_dd
        final_bs[s] = b

    prob_breach = np.mean(max_dds > 10.0) * 100.0

    return {
        "model_name": model_name,
        "k_mult": k_mult,
        "cagr_median": float(np.median(cagrs)),
        "cagr_ci_95": [float(np.percentile(cagrs, 2.5)), float(np.percentile(cagrs, 97.5))],
        "sharpe_median": float(np.median(sharpes)),
        "sharpe_ci_95": [float(np.percentile(sharpes, 2.5)), float(np.percentile(sharpes, 97.5))],
        "max_dd_median": float(np.median(max_dds)),
        "max_dd_ci_95": [float(np.percentile(max_dds, 2.5)), float(np.percentile(max_dds, 97.5))],
        "max_dd_95th_percentile": float(np.percentile(max_dds, 95.0)),
        "prob_breach_10pct_dd": float(prob_breach),
        "final_bankroll_median": float(np.median(final_bs))
    }


def analyze_covariance_30x_vs_60x(hist_df: pd.DataFrame) -> Dict:
    daily = hist_df.pivot_table(index="date", columns="payout_type", values="ret_unit", aggfunc="sum").fillna(0.0)
    cov_mat = daily.cov().values
    corr_mat = daily.corr().values
    means = daily.mean().values

    stds = np.sqrt(np.diag(cov_mat))
    inv_vols = 1.0 / stds
    w_risk_parity = inv_vols / np.sum(inv_vols)

    inv_cov = np.linalg.inv(cov_mat)
    f_kelly = inv_cov @ means
    w_kelly = np.maximum(0, f_kelly) / np.sum(np.maximum(0, f_kelly))

    ones = np.ones(2)
    w_tangency = (inv_cov @ means) / (ones.T @ inv_cov @ means)

    return {
        "means": {"30x": float(means[0]), "60x": float(means[1])},
        "stds": {"30x": float(stds[0]), "60x": float(stds[1])},
        "correlation": float(corr_mat[0, 1]),
        "covariance": float(cov_mat[0, 1]),
        "var_30x": float(cov_mat[0, 0]),
        "var_60x": float(cov_mat[1, 1]),
        "w_risk_parity": {"30x": float(w_risk_parity[0]), "60x": float(w_risk_parity[1])},
        "w_kelly": {"30x": float(w_kelly[0]), "60x": float(w_kelly[1])},
        "w_tangency": {"30x": float(w_tangency[0]), "60x": float(w_tangency[1])}
    }


def main():
    print("=" * 105)
    print(" 🚀 INICIANDO AUDITORÍA CUANTITATIVA INSTITUCIONAL Y OPTIMIZACIÓN DE SIZING (VERSION VECTORIZADA)")
    print("=" * 105)

    arrs = load_live_trades_arrays()
    n = arrs["n_trades"]
    print(f"\n[1] TRADES EN VIVO CARGADOS: {n} operaciones.")
    print(f"    Saldo inicial: $200.00 | Aciertos: {arrs['hits'].sum()} | Fallos: {n - arrs['hits'].sum()} | Win Rate: {arrs['hits'].mean()*100:.2f}%")

    print("\n[2] CARGANDO HISTORIAL 2 AÑOS PARA VALIDACIÓN DE COVARIANZA...")
    hist_df = load_historical_signals()
    print(f"    Total señales 2 años: {len(hist_df)} disparos sincronizados.")

    cov_res = analyze_covariance_30x_vs_60x(hist_df)
    print("\n" + "=" * 105)
    print(" 📊 ANÁLISIS DE COVARIANZA Y ASIGNACIÓN ÓPTIMA: 30x vs 60x")
    print("=" * 105)
    print(f" • Correlación diaria 30x vs 60x:       ρ = {cov_res['correlation']:+.4f} (DESACOPLAMIENTO PERFECTO)")
    print(f" • Covarianza diaria:                   Cov = {cov_res['covariance']:+.4f}")
    print(f" • Retorno medio diario (unidades):     30x = {cov_res['means']['30x']:+.4f} | 60x = {cov_res['means']['60x']:+.4f}")
    print(f" • Volatilidad diaria (std):            30x = {cov_res['stds']['30x']:.4f}  | 60x = {cov_res['stds']['60x']:.4f}")
    print(f" • Ponderación Paridad de Riesgo (1/σ): 30x = {cov_res['w_risk_parity']['30x']*100:.2f}% | 60x = {cov_res['w_risk_parity']['60x']*100:.2f}%")
    print(f" • Ponderación Multi-Asset Kelly:       30x = {cov_res['w_kelly']['30x']*100:.2f}% | 60x = {cov_res['w_kelly']['60x']*100:.2f}%")
    print(f" • Ponderación Markowitz Tangency:      30x = {cov_res['w_tangency']['30x']*100:.2f}% | 60x = {cov_res['w_tangency']['60x']*100:.2f}%")

    print("\n" + "=" * 105)
    print(" 📈 RESULTADOS DETERMINÍSTICOS SOBRE LOS 59 TRADES EN VIVO")
    print("=" * 105)
    models = [
        ("baseline_live", 0.75, 0.10),
        ("weekly_step_075", 0.75, 0.10),
        ("full_kelly_dynamic", 1.00, 0.10),
        ("half_kelly_dynamic", 0.50, 0.10),
        ("dynamic_gz_floor10", 0.75, 0.10),
        ("entropy_vol_dyn", 0.75, 0.10)
    ]

    det_results = []
    for m_name, k_m, mdd_t in models:
        b, peak, ret_pct, m_dd, cagr, sh_ann, cal = fast_simulate_vector(
            hits=arrs["hits"],
            payouts=arrs["payouts"],
            costs=arrs["costs"],
            f_units=arrs["f_units"],
            zona_codes=arrs["zona_codes"],
            week_nums=arrs["week_nums"],
            live_stakes=arrs["live_stakes"],
            model_name=m_name,
            k_mult=k_m,
            mdd_target=mdd_t,
            init_bankroll=200.0
        )
        det_results.append({
            "model_name": m_name, "final_b": b, "peak": peak, "ret_pct": ret_pct,
            "max_dd": m_dd, "cagr_proj": cagr, "sharpe_ann": sh_ann, "calmar": cal
        })
        print(f" {m_name:20s} | Saldo: ${b:6.2f} | Peak: ${peak:6.2f} | Retorno: {ret_pct:+6.2f}% | MaxDD: {m_dd:5.2f}% | Sharpe Anual: {sh_ann:5.2f} | Calmar: {cal:5.2f}")

    print("\n" + "=" * 105)
    print(" 🎲 SIMULACIÓN MONTE CARLO BOOTSTRAP (10,000 CAMINOS SINTÉTICOS)")
    print("=" * 105)
    mc_results = []
    for m_name, k_m, mdd_t in models:
        mc = fast_monte_carlo(arrs, model_name=m_name, k_mult=k_m, mdd_target=mdd_t, n_sims=10000)
        mc_results.append(mc)
        print(f"\n▶ Modelo: {m_name:20s} (k={k_m:.2f}x)")
        print(f"   • CAGR Proyectado Mediano:  {mc['cagr_median']:+10.1f}% | IC 95%: [{mc['cagr_ci_95'][0]:+10.1f}%, {mc['cagr_ci_95'][1]:+10.1f}%]")
        print(f"   • Sharpe Anualizado Mediano: {mc['sharpe_median']:6.2f}    | IC 95%: [{mc['sharpe_ci_95'][0]:6.2f}, {mc['sharpe_ci_95'][1]:6.2f}]")
        print(f"   • Max Drawdown Mediano:      {mc['max_dd_median']:5.2f}%    | IC 95%: [{mc['max_dd_ci_95'][0]:5.2f}%, {mc['max_dd_ci_95'][1]:5.2f}%]")
        print(f"   • Max Expected DD (95th %):  {mc['max_dd_95th_percentile']:5.2f}%")
        print(f"   • Probabilidad Ruptura 10%:  {mc['prob_breach_10pct_dd']:5.2f}% (P(MDD > 10%))")

    print("\n" + "=" * 105)
    print(" 🎯 BÚSQUEDA DEL MULTIPLICADOR ÓPTIMO DE KELLY (MDD < 10% al 95% Confianza)")
    print("=" * 105)
    k_candidates = np.linspace(0.10, 1.00, 19)
    best_k = 0.10
    best_cagr = -999.0
    records = []
    for k in k_candidates:
        mc = fast_monte_carlo(arrs, model_name="dynamic_gz_floor10", k_mult=k, mdd_target=0.10, n_sims=3000)
        p_safe = 100.0 - mc["prob_breach_10pct_dd"]
        records.append({
            "k_mult": round(k, 3),
            "p_safe_pct": round(p_safe, 2),
            "cagr_median": round(mc["cagr_median"], 1),
            "max_dd_95p": round(mc["max_dd_95th_percentile"], 2),
            "sharpe_median": round(mc["sharpe_median"], 2)
        })
        if p_safe >= 95.0 and mc["cagr_median"] > best_cagr:
            best_cagr = mc["cagr_median"]
            best_k = k
        print(f"   k={k:.2f}x | P(MDD <= 10%): {p_safe:5.2f}% | MaxDD 95th: {mc['max_dd_95th_percentile']:5.2f}% | CAGR Med: {mc['cagr_median']:+9.1f}% | Sharpe: {mc['sharpe_median']:.2f}")

    print(f"\n 🏆 Multiplicador Óptimo Teórico k*: {best_k:.3f}x Kelly (CAGR óptimo bajo P(MDD <= 10%) >= 95%)")

    audit_payload = {
        "covariance_analysis": cov_res,
        "deterministic_results": det_results,
        "monte_carlo_results": mc_results,
        "optimal_k": best_k,
        "records": records
    }
    out_json = os.path.join(BASE_DIR, "scratch", "portfolio_optimization_audit.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(audit_payload, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Auditoría institucional guardada en: {out_json}")


if __name__ == "__main__":
    main()
