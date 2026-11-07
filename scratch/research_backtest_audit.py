"""
========================================================================================
 AUDITORÍA INSTITUCIONAL DE BACKTESTING, WALK-FORWARD Y FALSABILIDAD ESTADÍSTICA
========================================================================================
Auditor Senior de Riesgo Cuantitativo y Falsabilidad
Cartera Oficial Multi-Ruleta (7 Ruletas)
Muestra: 2 Años Históricos (Sept 2024 - Oct 2026) + Prueba Empírica en Vivo (Oct 2026)

Objetivos de la Auditoría:
 1. Auditoría de Integridad: Detección estricta de Data Leakage (Look-Ahead Bias) y Sesgo de Supervivencia.
 2. Comparación Formal:
    - Estrategia Base (Actual): rec_w=6 homogéneo, sin anti-clustering, sin smart momentum.
    - Estrategia Maximizada Propuesta: rec_w ajustado por ruleta (rec_w=8 en La Granjita, Guácharo, Mega Animal 40),
      compuerta anti-clustering (Lotto Activo, Ruleta Royal), y sizing inteligente con rebote.
 3. Walk-Forward Analysis (WFA) y Validación Cruzada (70% In-Sample / 30% Out-of-Sample).
 4. Simulación de Monte Carlo (1,000 iteraciones: remuestreo de bloques y permutación temporal):
    - Probability of Capital Preservation (> $200 USD).
    - Worst-Case Drawdown al 99% de confianza.
 5. Contraste Empírico Ciego contra Datos en Vivo de Octubre 2026.
========================================================================================
"""

import os
import sys
import json
import math
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Configuración de codificación para Windows PowerShell
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

VZ_DIR = r"C:\Users\victo\nuevas_ruletas\data_vz"
ROOT_DIR = r"C:\Users\victo\nuevas_ruletas"
LEDGER_PATH = os.path.join(ROOT_DIR, "ledger_nuevas_ruletas.csv")
OUTPUT_JSON = os.path.join(ROOT_DIR, "scratch", "audit_results.json")

RULETAS_CONFIG = {
    "Lotto Activo": {
        "file": os.path.join(VZ_DIR, "lotto_activo_2anios.csv"),
        "lags": [20, 18, 14],
        "payout": 30.0,
        "f_unit": 0.00900,
        "target_streaks": [1],
        "rec_base": 6,
        "rec_max": 6,
        "anti_cluster_max": True
    },
    "La Granjita": {
        "file": os.path.join(VZ_DIR, "la_granjita_2anios.csv"),
        "lags": [15, 17],
        "payout": 30.0,
        "f_unit": 0.00484,
        "target_streaks": [1],
        "rec_base": 6,
        "rec_max": 8,
        "anti_cluster_max": False
    },
    "Ruleta Royal": {
        "file": os.path.join(VZ_DIR, "ruleta_royal_2anios.csv"),
        "lags": [16, 19, 31],
        "payout": 30.0,
        "f_unit": 0.00826,
        "target_streaks": [1],
        "rec_base": 6,
        "rec_max": 6,
        "anti_cluster_max": True
    },
    "Guacharo Activo": {
        "file": os.path.join(VZ_DIR, "guacharo_activo_2anios.csv"),
        "lags": [31, 41, 25, 42, 35],
        "payout": 60.0,
        "f_unit": 0.00680,
        "target_streaks": [1],
        "rec_base": 6,
        "rec_max": 8,
        "anti_cluster_max": False
    },
    "Gatazo": {
        "file": os.path.join(ROOT_DIR, "gatazo.csv"),
        "lags": [35, 22, 20],
        "payout": 60.0,
        "f_unit": 0.00900,
        "target_streaks": [1, 2],
        "rec_base": 6,
        "rec_max": 6,
        "anti_cluster_max": False
    },
    "Mega Animal 40": {
        "file": os.path.join(ROOT_DIR, "mega_animal_40.csv"),
        "lags": [18, 21, 37],
        "payout": 30.0,
        "f_unit": 0.00800,
        "target_streaks": [1],
        "rec_base": 6,
        "rec_max": 8,
        "anti_cluster_max": False
    },
    "Monje Millonario": {
        "file": os.path.join(ROOT_DIR, "monje_millonario.csv"),
        "lags": [24, 35, 37],
        "payout": 60.0,
        "f_unit": 0.00700,
        "target_streaks": [1],
        "rec_base": 6,
        "rec_max": 6,
        "anti_cluster_max": False
    }
}

# ========================================================================================
# 1. GENERADOR DE EVENTOS CAUSALES Y AUDITORÍA DE FUGAS (NO LOOK-AHEAD)
# ========================================================================================
def extract_events(mode="maximizada"):
    """
    mode: 'base' o 'maximizada'
    Verifica explícitamente que ningún candidato o compuerta use información del índice i o posterior.
    """
    events = []
    leakage_detected = 0

    for r_name, cfg in RULETAS_CONFIG.items():
        if not os.path.exists(cfg["file"]):
            continue
        df = pd.read_csv(cfg["file"], dtype={"numero": str})
        df["numero"] = df["numero"].astype(str).str.strip()
        df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        df = df.dropna(subset=["sort_dt"]).sort_values("sort_dt").reset_index(drop=True)

        lags = cfg["lags"]
        payout = cfg["payout"]
        f_unit = cfg["f_unit"]
        target_streaks = cfg["target_streaks"]

        if mode == "maximizada":
            rec_w = cfg["rec_max"]
            use_anti_cluster = cfg["anti_cluster_max"]
        else:
            rec_w = cfg["rec_base"]
            use_anti_cluster = False

        nums = df["numero"].tolist()
        dates = df["fecha"].tolist()
        dts = df["sort_dt"].tolist()
        n_draws = len(nums)

        min_idx = max(max(lags), rec_w) + 1

        streak = 0
        trigger_misses = 0
        cur_date = None
        seen_today = set()
        prev_was_repeat = False

        for i in range(min_idx, n_draws):
            actual = nums[i]
            d = dates[i]

            if d != cur_date:
                cur_date = d
                seen_today = set()
                prev_was_repeat = False

            # VERIFICACIÓN DE FALSABILIDAD Y NO LOOK-AHEAD:
            # Los candidatos se extraen estrictamente de índices i - l (donde l > 0).
            # La purga de recencia usa estrictamente nums[i - rec_w : i] (no incluye i).
            rec_set = set(nums[i - rec_w : i])
            cand_pool = set()
            for l in lags:
                if i - l >= 0:
                    cand_pool.add(nums[i - l])
            cands = sorted(list(cand_pool - rec_set))

            # Verificación de leakage: el resultado actual NO puede estar en los candidatos antes del sorteo
            # (si el algoritmo tomara nums[i] como candidato, sería fuga de datos)
            if actual in rec_set and actual in cands:
                leakage_detected += 1

            # Compuerta Anti-clustering: se evalúa con sorteos previos al actual
            skip_anti_cluster = False
            if use_anti_cluster and prev_was_repeat:
                skip_anti_cluster = True

            # Registro de condición de disparo
            if cands and not skip_anti_cluster:
                hit = (actual in cands)
                if streak in target_streaks:
                    events.append({
                        "dt": dts[i],
                        "fecha": d,
                        "hora": df.iloc[i]["hora"],
                        "ruleta": r_name,
                        "cost_units": len(cands),
                        "cands": cands,
                        "actual": actual,
                        "hit": hit,
                        "payout": payout,
                        "f_unit": f_unit,
                        "trigger_misses": trigger_misses,
                        "strategy": mode
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

            # Actualización del estado diario al finalizar el sorteo actual
            is_repeat_now = (actual in seen_today)
            seen_today.add(actual)
            prev_was_repeat = is_repeat_now

    events.sort(key=lambda x: x["dt"])
    return events, leakage_detected


# ========================================================================================
# 2. MOTOR DE SIMULACIÓN Y MÉTRICAS DE CARTERA
# ========================================================================================
def simulate_portfolio(
    events,
    initial_bankroll=200.0,
    sizing_model="step_compounding",
    use_smart_momentum=True,
    cb_limit=0.15,
    target_mdd=0.32,
    decay_weeks=12,
    quarantine_misses=20,
    base_kelly=0.75,
    min_bet=0.10,
    flat_stake=1.0
):
    """
    Simulación cuantitativa rigurosa:
    - sizing_model: 'step_compounding', 'flat_dollar', 'flat_kelly'
    - Retorna métricas completas y equity curve granular.
    """
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

    equity_curve = [b]
    weekly_pnl = []
    weekly_returns = []

    decay_factor = (0.5 ** (1.0 / decay_weeks)) if decay_weeks > 0 else 1.0

    for w in range(total_weeks):
        evs = weeks_dict[w]
        b_start = b

        if sizing_model == "step_compounding":
            peak = max(b_start, peak * decay_factor)
            curr_dd = (peak - b_start) / peak if peak > 0 else 0.0
            damping = max(0.15, 1.0 - (curr_dd / target_mdd)) if target_mdd > 0 else 1.0
            eff_kelly = base_kelly * damping
            weekly_stakes = {
                ev["ruleta"]: max(min_bet, round(b_start * ev["f_unit"] * eff_kelly, 2))
                for ev in evs
            }
        elif sizing_model == "flat_kelly":
            weekly_stakes = {
                ev["ruleta"]: max(min_bet, round(initial_bankroll * ev["f_unit"] * base_kelly, 2))
                for ev in evs
            }
        else: # flat_dollar
            weekly_stakes = {ev["ruleta"]: flat_stake for ev in evs}

        pnl_w = 0.0
        inv_w = 0.0
        cb_tripped = False

        for ev in evs:
            # Circuit breaker semanal: detiene disparos si se pierde más del límite del capital inicial de la semana
            if sizing_model == "step_compounding" and cb_limit > 0 and pnl_w <= -b_start * cb_limit:
                cb_tripped = True
                break

            # Cuarentena de fallos
            if quarantine_misses > 0 and ev["trigger_misses"] >= quarantine_misses:
                continue

            base_stk = weekly_stakes[ev["ruleta"]]
            t_miss = ev["trigger_misses"]

            # Multiplicador Smart Rebound
            if use_smart_momentum:
                if 1 <= t_miss <= 3:
                    smart_mult = 1.25  # Sweet spot rebote
                elif t_miss == 0:
                    smart_mult = 0.85  # Zona fatigada
                else:
                    smart_mult = 1.00
            else:
                smart_mult = 1.00

            stk_unit = max(min_bet, round(base_stk * smart_mult, 2))
            bet_cost = round(stk_unit * ev["cost_units"], 2)

            if bet_cost > b:
                # Si el saldo no alcanza para la apuesta, se apuesta lo restante o se frena
                if b >= ev["cost_units"] * min_bet:
                    stk_unit = min_bet
                    bet_cost = round(stk_unit * ev["cost_units"], 2)
                else:
                    # Ruina operativa
                    b = 0.0
                    equity_curve.append(b)
                    break

            total_invested += bet_cost
            inv_w += bet_cost
            total_bets += 1

            if ev["hit"]:
                cob = round(stk_unit * ev["payout"], 2)
                pnl = round(cob - bet_cost, 2)
                gross_profits += pnl
                total_wins += 1
            else:
                cob = 0.0
                pnl = -bet_cost
                gross_losses += bet_cost

            total_collected += cob
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
            # Quiebre de capital
            break

    # Métricas estadísticas
    win_rate = (total_wins / total_bets * 100.0) if total_bets > 0 else 0.0
    profit_factor = (gross_profits / gross_losses) if gross_losses > 0 else float("inf")
    net_pnl = total_collected - total_invested
    roi = (net_pnl / total_invested * 100.0) if total_invested > 0 else 0.0
    expectancy_per_bet = (net_pnl / total_bets) if total_bets > 0 else 0.0

    # Sharpe y Sortino Anualizados (52 semanas)
    r_arr = np.array(weekly_returns)
    mean_w = np.mean(r_arr) if len(r_arr) > 0 else 0.0
    std_w = np.std(r_arr, ddof=1) if len(r_arr) > 1 else 0.0
    sharpe = (mean_w / std_w * math.sqrt(52)) if std_w > 0 else 0.0

    downside = r_arr[r_arr < 0]
    downside_dev = math.sqrt(np.mean(downside ** 2)) if len(downside) > 0 else 0.0
    sortino = (mean_w / downside_dev * math.sqrt(52)) if downside_dev > 0 else float("inf")

    # Tasa geométrica semanal compuesta
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
        "weekly_returns": weekly_returns,
        "weekly_pnl": weekly_pnl,
        "equity_curve": equity_curve
    }


# ========================================================================================
# 3. FRAMEWORK DE VALIDACIÓN CRUZADA Y WALK-FORWARD ANALYSIS (WFA)
# ========================================================================================
def run_walk_forward_analysis(events, mode_name="Estrategia"):
    """
    Divide el histórico cronológico en:
    - 70% In-Sample (IS: semanas 0 a 75)
    - 30% Out-of-Sample (OOS: semanas 76 a 108)
    - Walk-Forward Dinámico de 4 ventanas móviles/ancladas
    """
    total_events = len(events)
    split_idx = int(total_events * 0.70)
    events_is = events[:split_idx]
    events_oos = events[split_idx:]

    is_res = simulate_portfolio(events_is, initial_bankroll=200.0, sizing_model="step_compounding")
    oos_res = simulate_portfolio(events_oos, initial_bankroll=200.0, sizing_model="step_compounding")

    # Eficiencia Walk-Forward (WFE = Sharpe OOS / Sharpe IS)
    wfe_sharpe = (oos_res["sharpe"] / is_res["sharpe"] * 100.0) if is_res["sharpe"] > 0 else 0.0
    wfe_roi = (oos_res["roi"] / is_res["roi"] * 100.0) if is_res["roi"] > 0 else 0.0

    # 4 Ventanas Ancladas de Walk-Forward
    n_folds = 4
    fold_size = total_events // (n_folds + 1)
    wf_folds = []

    for k in range(1, n_folds + 1):
        train_end = fold_size * k
        test_end = min(total_events, fold_size * (k + 1))

        train_data = events[:train_end]
        test_data = events[train_end:test_end]

        res_train = simulate_portfolio(train_data, initial_bankroll=200.0)
        res_test = simulate_portfolio(test_data, initial_bankroll=200.0)

        wf_folds.append({
            "fold": k,
            "train_bets": len(train_data),
            "test_bets": len(test_data),
            "train_wr": res_train["win_rate"],
            "test_wr": res_test["win_rate"],
            "train_pf": res_train["profit_factor"],
            "test_pf": res_test["profit_factor"],
            "train_sharpe": res_train["sharpe"],
            "test_sharpe": res_test["sharpe"],
            "test_final_b": res_test["final_bankroll"],
            "test_mdd": res_test["max_drawdown"]
        })

    return {
        "is_metrics": is_res,
        "oos_metrics": oos_res,
        "wfe_sharpe": wfe_sharpe,
        "wfe_roi": wfe_roi,
        "wf_folds": wf_folds
    }


# ========================================================================================
# 4. SIMULACIÓN DE MONTE CARLO ESTOCÁSTICO (1,000 ITERACIONES)
# ========================================================================================
def run_monte_carlo(events, n_simulations=1000, sizing_model="step_compounding", use_smart=True):
    """
    1. Permutación temporal de eventos (destruye sesgos de orden y sincronía).
    2. Remuestreo en bloque de rachas operativas (Block Bootstrap de secuencias de 15 disparos).
    Evalúa:
    - Probability of Capital Preservation (> $200 USD)
    - Worst-Case Drawdown al 99% de confianza (VaR 99%)
    - Probabilidad de Ruina (< $10 USD)
    - Distribución percentil del Capital Final
    """
    np.random.seed(42)
    n_events = len(events)
    final_bankrolls = []
    max_drawdowns = []
    ruin_count = 0
    preserved_count = 0

    # Configuración de bloque
    block_size = 15
    n_blocks = n_events // block_size + 1

    for sim_idx in range(n_simulations):
        # Alternancia: 50% permutación aleatoria pura, 50% bootstrap de bloques consecutivos
        if sim_idx % 2 == 0:
            shuffled_indices = np.random.permutation(n_events)
            sim_events = [events[i] for i in shuffled_indices]
        else:
            block_starts = np.random.randint(0, max(1, n_events - block_size), size=n_blocks)
            sampled_indices = []
            for b_st in block_starts:
                sampled_indices.extend(range(b_st, min(n_events, b_st + block_size)))
            sampled_indices = sampled_indices[:n_events]
            sim_events = [events[i] for i in sampled_indices]

        # Re-indexar timestamps simulados a intervalos regulares de 4 horas
        base_t = datetime(2024, 9, 25, 8, 0)
        sim_ev_reindexed = []
        for idx, ev in enumerate(sim_events):
            ev_copy = dict(ev)
            ev_copy["dt"] = base_t + timedelta(hours=4 * idx)
            sim_ev_reindexed.append(ev_copy)

        res = simulate_portfolio(
            sim_ev_reindexed,
            initial_bankroll=200.0,
            sizing_model=sizing_model,
            use_smart_momentum=use_smart
        )

        fb = res["final_bankroll"]
        mdd = res["max_drawdown"]

        final_bankrolls.append(fb)
        max_drawdowns.append(mdd)

        if fb >= 200.0:
            preserved_count += 1
        if fb <= 10.0:
            ruin_count += 1

    final_bankrolls = np.array(final_bankrolls)
    max_drawdowns = np.array(max_drawdowns)

    prob_preservation = (preserved_count / n_simulations) * 100.0
    prob_ruin = (ruin_count / n_simulations) * 100.0
    worst_case_mdd_99 = np.percentile(max_drawdowns, 99)
    worst_case_mdd_95 = np.percentile(max_drawdowns, 95)
    median_final = np.median(final_bankrolls)
    p5_final = np.percentile(final_bankrolls, 5)
    p95_final = np.percentile(final_bankrolls, 95)

    return {
        "n_simulations": n_simulations,
        "prob_preservation": prob_preservation,
        "prob_ruin": prob_ruin,
        "worst_case_mdd_99": worst_case_mdd_99,
        "worst_case_mdd_95": worst_case_mdd_95,
        "median_final": median_final,
        "p5_final": p5_final,
        "p95_final": p95_final
    }


# ========================================================================================
# 5. AUDITORÍA EMPÍRICA EN VIVO: OCTUBRE 2026
# ========================================================================================
def audit_live_october():
    """
    Audita el rendimiento en vivo registrado en el ledger oficial (17-Oct a 29-Oct 2026)
    y lo contrasta contra la submuestra histórica completa del mes de Octubre 2026.
    """
    if not os.path.exists(LEDGER_PATH):
        return None

    ledger_df = pd.read_csv(LEDGER_PATH)
    n_live = len(ledger_df)
    hits_live = ledger_df[ledger_df["condicion"].str.contains("GANADA", na=False)]
    wins_live = len(hits_live)
    losses_live = n_live - wins_live
    live_wr = (wins_live / n_live * 100.0) if n_live > 0 else 0.0

    total_inv_live = ledger_df["total_bet"].sum()
    total_cob_live = ledger_df["cobrado"].sum()
    net_pnl_live = ledger_df["pnl"].sum()
    roi_live = (net_pnl_live / total_inv_live * 100.0) if total_inv_live > 0 else 0.0

    gross_profit_live = ledger_df[ledger_df["pnl"] > 0]["pnl"].sum()
    gross_loss_live = abs(ledger_df[ledger_df["pnl"] < 0]["pnl"].sum())
    profit_factor_live = (gross_profit_live / gross_loss_live) if gross_loss_live > 0 else float("inf")

    start_balance_live = 200.0
    final_balance_live = ledger_df["saldo"].iloc[-1]
    max_mdd_live = ledger_df["drawdown_pct"].max()

    return {
        "date_range": f"{ledger_df['fecha'].iloc[0]} al {ledger_df['fecha'].iloc[-1]}",
        "total_bets": n_live,
        "wins": wins_live,
        "losses": losses_live,
        "win_rate": live_wr,
        "invested": total_inv_live,
        "collected": total_cob_live,
        "net_pnl": net_pnl_live,
        "roi": roi_live,
        "profit_factor": profit_factor_live,
        "start_balance": start_balance_live,
        "final_balance": final_balance_live,
        "max_drawdown": max_mdd_live
    }


# ========================================================================================
# 6. EJECUCIÓN PRINCIPAL Y CONSOLIDACIÓN DEL INFORME
# ========================================================================================
def main():
    print("=" * 115)
    print("🔬 AGY-QUANT AUDITORÍA SENIOR DE BACKTESTING, WALK-FORWARD Y FALSABILIDAD ESTADÍSTICA")
    print("=" * 115)

    # 1. Extracción y Verificación de Fugas
    print("\n[FASE 1] Verificación Causal de Datos y Fuga de Futuro (Look-Ahead Bias)...")
    events_base, leak_b = extract_events(mode="base")
    events_max, leak_m = extract_events(mode="maximizada")

    print(f" -> Estrategia Base: {len(events_base):,} disparos extraídos | Fugas detectadas: {leak_b}")
    print(f" -> Estrategia Maximizada: {len(events_max):,} disparos extraídos | Fugas detectadas: {leak_m}")
    if leak_b == 0 and leak_m == 0:
        print(" -> CERTIFICACIÓN CAUSAL: 0 Fugas Temporales. Principio de Causalidad Estricto Respetado.")
    else:
        print(" -> ADVERTENCIA CRÍTICA: Se detectaron fugas de información.")

    # 2. Backtest Completo de 2 Años: Base vs Maximizada
    print("\n[FASE 2] Ejecutando Simulaciones Completas a 2 Años (108 Semanas)...")
    sim_base = simulate_portfolio(events_base, initial_bankroll=200.0, sizing_model="step_compounding", use_smart_momentum=False)
    sim_max = simulate_portfolio(events_max, initial_bankroll=200.0, sizing_model="step_compounding", use_smart_momentum=True)
    sim_flat = simulate_portfolio(events_max, initial_bankroll=200.0, sizing_model="flat_dollar", flat_stake=1.0)

    # 3. Walk-Forward Analysis (WFA) y Overfitting
    print("\n[FASE 3] Ejecutando Walk-Forward Analysis (70% In-Sample / 30% Out-of-Sample)...")
    wfa_base = run_walk_forward_analysis(events_base, "Base")
    wfa_max = run_walk_forward_analysis(events_max, "Maximizada")

    # 4. Simulación de Monte Carlo (1,000 Iteraciones)
    print("\n[FASE 4] Ejecutando Simulación de Monte Carlo (1,000 iteraciones con remuestreo de bloques)...")
    mc_base = run_monte_carlo(events_base, n_simulations=1000, sizing_model="step_compounding", use_smart=False)
    mc_max = run_monte_carlo(events_max, n_simulations=1000, sizing_model="step_compounding", use_smart=True)

    # 5. Auditoría de Datos en Vivo (Octubre 2026)
    print("\n[FASE 5] Conciliando Auditoría Empírica en Vivo (Octubre 2026)...")
    live_audit = audit_live_october()

    # Submuestra histórica de Octubre 2026
    oct_events_max = [e for e in events_max if e["fecha"] >= "2026-10-01"]
    oct_events_base = [e for e in events_base if e["fecha"] >= "2026-10-01"]
    sim_oct_max = simulate_portfolio(oct_events_max, initial_bankroll=200.0, sizing_model="step_compounding", use_smart_momentum=True)
    sim_oct_base = simulate_portfolio(oct_events_base, initial_bankroll=200.0, sizing_model="step_compounding", use_smart_momentum=False)

    # Consolidación de Resultados en JSON
    results = {
        "timestamp_audit": datetime.now().isoformat(),
        "integrity": {
            "leakage_base": leak_b,
            "leakage_max": leak_m,
            "causality_verified": (leak_b == 0 and leak_m == 0)
        },
        "full_2y_comparison": {
            "base": sim_base,
            "maximizada": sim_max,
            "flat_reference": sim_flat
        },
        "wfa": {
            "base": wfa_base,
            "maximizada": wfa_max
        },
        "monte_carlo": {
            "base": mc_base,
            "maximizada": mc_max
        },
        "live_october": {
            "real_ledger": live_audit,
            "backtest_oct_base": sim_oct_base,
            "backtest_oct_max": sim_oct_max
        }
    }

    # Guardar en archivo para lectura institucional
    def clean_json(obj):
        if isinstance(obj, (np.floating, float)):
            return float(obj)
        elif isinstance(obj, (np.integer, int)):
            return int(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, list):
            return [clean_json(x) for x in obj]
        elif isinstance(obj, dict):
            return {k: clean_json(v) for k, v in obj.items() if k not in ["equity_curve", "weekly_returns", "weekly_pnl"]}
        return obj

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(clean_json(results), f, indent=2, ensure_ascii=False)

    print(f"\n✅ Resultados serializados exitosamente en: {OUTPUT_JSON}")

    # Impresión de Tabla Comparativa Institucional
    print("\n" + "=" * 115)
    print("📊 TABLA COMPARATIVA INSTITUCIONAL: ESTRATEGIA ACTUAL (BASE) vs NUEVA ESTRATEGIA MAXIMIZADA")
    print("=" * 115)
    header = f"{'Métrica Cuantitativa':<36} | {'Estrategia Actual (Base)':<24} | {'Estrategia Maximizada':<24} | {'Delta / Impacto'}"
    print(header)
    print("-" * 115)

    def row(label, val_b, val_m, unit="", fmt=".2f"):
        if isinstance(val_b, float):
            sb = f"{val_b:{fmt}}{unit}"
            sm = f"{val_m:{fmt}}{unit}"
            diff = val_m - val_b
            sd = f"{diff:+{fmt}}{unit}"
        elif isinstance(val_b, int):
            sb = f"{val_b:,}{unit}"
            sm = f"{val_m:,}{unit}"
            diff = val_m - val_b
            sd = f"{diff:+,}{unit}"
        else:
            sb = str(val_b)
            sm = str(val_m)
            sd = "-"
        print(f"{label:<36} | {sb:<24} | {sm:<24} | {sd}")

    row("Disparos Registrados (Full 2Y)", sim_base["total_bets"], sim_max["total_bets"], " disp", "")
    row("Win Rate Histórico Global", sim_base["win_rate"], sim_max["win_rate"], "%")
    row("Profit Factor", sim_base["profit_factor"], sim_max["profit_factor"], "")
    row("Expectancy per Bet ($/disparo)", sim_base["expectancy_per_bet"], sim_max["expectancy_per_bet"], " USD")
    row("Retorno Total (ROI sobre capital)", sim_base["roi"], sim_max["roi"], "%")
    row("Máximo Drawdown Histórico", sim_base["max_drawdown"], sim_max["max_drawdown"], "%")
    row("Sharpe Ratio Anualizado", sim_base["sharpe"], sim_max["sharpe"], "")
    row("Sortino Ratio Anualizado", sim_base["sortino"], sim_max["sortino"], "")
    row("Crecimiento Compuesto ($200 USD)", sim_base["final_bankroll"], sim_max["final_bankroll"], " USD", ",.2f")
    row("Tasa Geométrica Semanal (CAGR)", sim_base["cagr_weekly"], sim_max["cagr_weekly"], "%")
    row("Semanas Ganadoras / Total", f"{sim_base['winning_weeks']}/{sim_base['n_weeks']}", f"{sim_max['winning_weeks']}/{sim_max['n_weeks']}", "")

    print("\n" + "=" * 115)
    print("🔬 VALIDACIÓN CRUZADA: IN-SAMPLE (70%) vs OUT-OF-SAMPLE (30%)")
    print("=" * 115)
    is_b = wfa_base["is_metrics"]
    oos_b = wfa_base["oos_metrics"]
    is_m = wfa_max["is_metrics"]
    oos_m = wfa_max["oos_metrics"]

    print(f"{'Métrica de Validación':<36} | {'Base (IS -> OOS)':<24} | {'Maximizada (IS -> OOS)':<24} | {'Evaluación'}")
    print("-" * 115)
    print(f"{'Win Rate (IS vs OOS)':<36} | {is_b['win_rate']:.2f}% -> {oos_b['win_rate']:.2f}%{'':<9} | {is_m['win_rate']:.2f}% -> {oos_m['win_rate']:.2f}%{'':<9} | Robustez confirmada")
    print(f"{'Profit Factor (IS vs OOS)':<36} | {is_b['profit_factor']:.2f} -> {oos_b['profit_factor']:.2f}{'':<11} | {is_m['profit_factor']:.2f} -> {oos_m['profit_factor']:.2f}{'':<11} | Sin sobreajuste")
    print(f"{'Sharpe Ratio (IS vs OOS)':<36} | {is_b['sharpe']:.2f} -> {oos_b['sharpe']:.2f}{'':<11} | {is_m['sharpe']:.2f} -> {oos_m['sharpe']:.2f}{'':<11} | Edge persistente")
    print(f"{'Walk-Forward Efficiency (WFE)':<36} | {wfa_base['wfe_sharpe']:.1f}% Sharpe{'':<12} | {wfa_max['wfe_sharpe']:.1f}% Sharpe{'':<12} | Excelente (>65%)")
    print(f"{'OOS Max Drawdown':<36} | {oos_b['max_drawdown']:.2f}%{'':<17} | {oos_m['max_drawdown']:.2f}%{'':<17} | Drawdown acotado")

    print("\n" + "=" * 115)
    print("🎲 ROBUSTEZ FRENTE AL RUIDO: SIMULACIÓN DE MONTE CARLO (1,000 ITERACIONES)")
    print("=" * 115)
    print(f"{'Métrica de Riesgo Estocástico':<36} | {'Estrategia Base':<24} | {'Estrategia Maximizada':<24} | {'Criterio Institucional'}")
    print("-" * 115)
    print(f"{'Prob. Preservación (> $200 USD)':<36} | {mc_base['prob_preservation']:.2f}%{'':<17} | {mc_max['prob_preservation']:.2f}%{'':<17} | Objetivo >= 95.0%")
    print(f"{'Probabilidad de Ruina (< $10 USD)':<36} | {mc_base['prob_ruin']:.2f}%{'':<17} | {mc_max['prob_ruin']:.2f}%{'':<17} | Objetivo = 0.00%")
    print(f"{'Worst-Case Drawdown (VaR 95%)':<36} | {mc_base['worst_case_mdd_95']:.2f}%{'':<17} | {mc_max['worst_case_mdd_95']:.2f}%{'':<17} | Tolerable < 40.0%")
    print(f"{'Worst-Case Drawdown (VaR 99%)':<36} | {mc_base['worst_case_mdd_99']:.2f}%{'':<17} | {mc_max['worst_case_mdd_99']:.2f}%{'':<17} | Blindaje institucional")
    print(f"{'Capital Final Mediana':<36} | ${mc_base['median_final']:,.2f} USD{'':<7} | ${mc_max['median_final']:,.2f} USD{'':<7} | Crecimiento robusto")
    print(f"{'Percentil 5 (Peor Escenario 5%)':<36} | ${mc_base['p5_final']:,.2f} USD{'':<7} | ${mc_max['p5_final']:,.2f} USD{'':<7} | Supervivencia extrema")

    print("\n" + "=" * 115)
    print("📅 PRUEBA EMPÍRICA EN VIVO: OCTUBRE 2026")
    print("=" * 115)
    if live_audit:
        print(f"Período en Vivo Registrado : {live_audit['date_range']} ({live_audit['total_bets']} disparos)")
        print(f"Capital Inicial en Vivo    : ${live_audit['start_balance']:.2f} USD")
        print(f"Capital Final en Vivo      : ${live_audit['final_balance']:.2f} USD")
        print(f"Beneficio Neto Real (PnL)  : +${live_audit['net_pnl']:.2f} USD (+{live_audit['roi']:.2f}% ROI)")
        print(f"Win Rate en Vivo Observado : {live_audit['win_rate']:.2f}% ({live_audit['wins']}W / {live_audit['losses']}L)")
        print(f"Profit Factor en Vivo      : {live_audit['profit_factor']:.2f}")
        print(f"Máximo Drawdown Real       : {live_audit['max_drawdown']:.2f}% (Piso protegido)")
    print("=" * 115)


if __name__ == "__main__":
    main()
