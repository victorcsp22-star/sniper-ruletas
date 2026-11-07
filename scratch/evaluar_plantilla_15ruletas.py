"""
Sistema de Análisis Exhaustivo y Comparativa Cuantitativa Multiruleta (15 ruletas).
Evalúa para cada ruleta:
1. Payout teórico (30x vs 60x u otro)
2. Autocorrelación de Lags (Top 5 lags con mayor lift estadístico)
3. Matriz de Markov (pares contiguos con mayor probabilidad de transición)
4. Tasa de repetición intradía (Anti-clustering suitability)
5. Simulación de rendimiento del Gatillo Sniper (Racha 1 post-fallo con ventana de exclusión)
6. Sharpe / Profit Factor / Win Rate / Max Drawdown histórico
7. Veredicto del Agente Cuantitativo (APROBADA, RECHAZADA, CONDICIONADA)
"""

import os, datetime, math
import pandas as pd
import numpy as np

RULETAS_DATA = {
    "Guacharo Activo": (r"C:\Users\victo\nuevas_ruletas\data_vz\guacharo_activo_2anios.csv", 60.0, 75),
    "Ruleta Royal": (r"C:\Users\victo\nuevas_ruletas\data_vz\ruleta_royal_2anios.csv", 30.0, 38),
    "El Guacharito Millonario": (r"C:\Users\victo\nuevas_ruletas\data_vz\guacharito_millonario_2anios.csv", 60.0, 75),
    "Lotto Activo": (r"C:\Users\victo\nuevas_ruletas\data_vz\lotto_activo_2anios.csv", 30.0, 38),
    "Lotto Activo RD Internacional": (r"C:\Users\victo\nuevas_ruletas\lotto_activo_rd_lotoven_completo.csv", 30.0, 38),
    "Selva Plus": (r"C:\Users\victo\nuevas_ruletas\data_vz\selva_plus_2anios.csv", 30.0, 38),
    "Granja Millonaria - Granjazo": (r"C:\Users\victo\nuevas_ruletas\granja_millonaria_granjazo.csv", 60.0, 75),
    "La Granjita": (r"C:\Users\victo\nuevas_ruletas\data_vz\la_granjita_2anios.csv", 30.0, 38),
    "Monje Millonario": (r"C:\Users\victo\nuevas_ruletas\monje_millonario.csv", 60.0, 75),
    "Loto Chaima": (r"C:\Users\victo\nuevas_ruletas\loto_chaima.csv", 60.0, 75),
    "Granja Millonaria - Animalitos": (r"C:\Users\victo\nuevas_ruletas\granja_millonaria_animalitos.csv", 30.0, 38),
    "Gatazo": (r"C:\Users\victo\nuevas_ruletas\gatazo.csv", 60.0, 75),
    "Mega Animal 40": (r"C:\Users\victo\nuevas_ruletas\mega_animal_40.csv", 30.0, 40),
    "Tropi Gana": (r"C:\Users\victo\nuevas_ruletas\tropi_gana.csv", 30.0, 38),
    "Lotto Gato": (r"C:\Users\victo\nuevas_ruletas\lotto_gato.csv", 60.0, 75),
}

def analyze_roulette(name, fpath, payout, total_animals):
    if not os.path.exists(fpath):
        return None
    df = pd.read_csv(fpath)
    if len(df) < 50:
        return {
            "name": name, "filas": len(df), "status": "RECHAZADA",
            "motivo": "Muestra insuficiente (<50 sorteos)"
        }
    
    # Ordenar cronológicamente
    if "fecha" in df.columns and "hora" in df.columns:
        df["dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], errors="coerce")
        df = df.sort_values(by="dt").dropna(subset=["numero"]).reset_index(drop=True)
    
    nums = [str(x).strip() for x in df["numero"].tolist()]
    dates = df["fecha"].astype(str).tolist() if "fecha" in df.columns else [""] * len(nums)
    N = len(nums)

    # 1. Tasa aleatoria base
    p_rand = 1.0 / total_animals
    
    # 2. Análisis de Lags (1 a 50)
    lag_lifts = {}
    for l in range(1, min(50, N - 10)):
        hits = 0
        trials = N - l
        for i in range(l, N):
            if nums[i] == nums[i - l]:
                hits += 1
        emp_rate = hits / trials if trials > 0 else 0
        lift = (emp_rate / p_rand) if p_rand > 0 else 1.0
        lag_lifts[l] = lift

    # Top 3 lags con mayor lift (con l >= 6 para dar tiempo de recencia)
    candidate_lags = [(l, lift) for l, lift in lag_lifts.items() if l >= 6]
    candidate_lags.sort(key=lambda x: x[1], reverse=True)
    best_lags = [l for l, _ in candidate_lags[:3]] if candidate_lags else [14, 18, 20]

    # 3. Análisis de Markov (pares recurrentes)
    pair_counts = {}
    for i in range(1, N):
        p = (nums[i-1], nums[i])
        pair_counts[p] = pair_counts.get(p, 0) + 1
    
    top_markov = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    strong_markov = {pair[0]: pair[1] for pair, cnt in top_markov if cnt >= 5}

    # 4. Anti-clustering (duplicados intradía)
    dups_today = 0
    total_draws_same_day = 0
    cur_date = None
    seen_day = set()
    for i in range(N):
        d = dates[i]
        if d != cur_date:
            cur_date = d
            seen_day = set()
        else:
            total_draws_same_day += 1
            if nums[i] in seen_day:
                dups_today += 1
        seen_day.add(nums[i])
    dup_pct = (dups_today / total_draws_same_day * 100) if total_draws_same_day > 0 else 0.0

    # 5. Backtest Sniper Simulado (Racha 1, rec_w=6)
    rec_w = 6
    streak = 0
    ops = 0
    wins = 0
    total_invested = 0.0
    total_collected = 0.0
    max_streak_loss = 0
    cur_streak_loss = 0
    daily_pnls = {}

    for i in range(max(best_lags) + rec_w, N):
        actual = nums[i]
        rec_set = set(nums[i-rec_w:i])
        cands = list({nums[i-l] for l in best_lags} - rec_set)

        if streak == 1 and cands:
            ops += 1
            cost = len(cands) * 1.0
            total_invested += cost
            hit = (actual in cands)
            pnl_op = -cost
            if hit:
                wins += 1
                cur_streak_loss = 0
                cobrado = payout * 1.0
                total_collected += cobrado
                pnl_op += cobrado
            else:
                cur_streak_loss += 1
                max_streak_loss = max(max_streak_loss, cur_streak_loss)

            d = dates[i]
            daily_pnls[d] = daily_pnls.get(d, 0.0) + pnl_op

        # Actualizar streak real
        if cands:
            streak = 0 if actual in cands else streak + 1

    net_pnl = total_collected - total_invested
    roi = (net_pnl / total_invested * 100.0) if total_invested > 0 else 0.0
    win_rate = (wins / ops * 100.0) if ops > 0 else 0.0
    profit_factor = (total_collected / total_invested) if total_invested > 0 else 0.0

    # Drawdown máximo
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    for d, p in sorted(daily_pnls.items()):
        cum += p
        peak = max(peak, cum)
        dd = peak - cum
        max_dd = max(max_dd, dd)

    # Veredicto
    status = "APROBADA"
    motivo = "Patrón robusto y EV altamente positivo"
    if N < 1500:
        status = "CONDICIONADA"
        motivo = f"Historial corto ({N} sorteos) aunque positivo"
    if roi < 10.0 or profit_factor < 1.10:
        status = "RECHAZADA"
        motivo = f"ROI o PF insuficiente (ROI={roi:.1f}%, PF={profit_factor:.2f})"
    if max_streak_loss > 30:
        status = "RIESGO_ALTO"
        motivo = f"Racha perdedora prolongada (MaxL={max_streak_loss})"

    return {
        "name": name,
        "filas": N,
        "payout": payout,
        "total_animals": total_animals,
        "dup_pct": round(dup_pct, 1),
        "best_lags": best_lags,
        "ops": ops,
        "wins": wins,
        "win_rate": round(win_rate, 2),
        "invested": round(total_invested, 2),
        "collected": round(total_collected, 2),
        "net_pnl": round(net_pnl, 2),
        "roi": round(roi, 2),
        "profit_factor": round(profit_factor, 2),
        "max_streak_loss": max_streak_loss,
        "max_dd": round(max_dd, 2),
        "status": status,
        "motivo": motivo
    }

print("Ejecutando análisis cuantitativo de las 15 ruletas...")
results = []
for name, (path, payout, n_anim) in RULETAS_DATA.items():
    res = analyze_roulette(name, path, payout, n_anim)
    if res:
        results.append(res)

df_res = pd.DataFrame(results)
df_res.to_csv(r"C:\Users\victo\nuevas_ruletas\scratch\analisis_comparativo_15ruletas.csv", index=False)
print("Análisis completado y guardado.")
