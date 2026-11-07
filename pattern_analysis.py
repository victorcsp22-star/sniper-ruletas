"""
========================================================================================
 ANÁLISIS DE CONSTANCIA DEL PATRÓN SNIPER Y AUTOCORRELACIÓN EN NUEVAS RULETAS
========================================================================================
Analiza las 7 ruletas descargadas:
 1. Loto Chaima
 2. Lotto Gato
 3. Gatazo
 4. Mega Animal 40
 5. Monje Millonario
 6. Granja Millonaria - Animalitos
 7. Granja Millonaria - Granjazo

Metodología:
 1. Escaneo exhaustivo de lags de repetición (Lag 1 al 40) con exclusión de recencia 6h.
 2. Identificación de los mejores lags y comparación vs tasa aleatoria (1/N).
 3. Comprobación del efecto rebote del Gatillo Sniper Post-Fallo 1 (P(Acierto | Racha=1)).
 4. Backtest simulado con apuesta fija de $1.00 USD por animal para medir PnL y ROI.
 5. Diagnóstico de constancia y viabilidad.
========================================================================================
"""

import os
import sys
import pandas as pd
import numpy as np

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DATA_DIR = r"C:\Users\victo\nuevas_ruletas"

CONFIG = {
    "Loto Chaima": {
        "file": os.path.join(DATA_DIR, "loto_chaima.csv"),
        "total_animals": 57,
        "payout": 40.0,
        "emoji": "🦜"
    },
    "Lotto Gato": {
        "file": os.path.join(DATA_DIR, "lotto_gato.csv"),
        "total_animals": 47,
        "payout": 30.0,
        "emoji": "🐱"
    },
    "Gatazo": {
        "file": os.path.join(DATA_DIR, "gatazo.csv"),
        "total_animals": 85,
        "payout": 60.0,
        "emoji": "🐯"
    },
    "Mega Animal 40": {
        "file": os.path.join(DATA_DIR, "mega_animal_40.csv"),
        "total_animals": 47,
        "payout": 30.0,
        "emoji": "🦏"
    },
    "Monje Millonario": {
        "file": os.path.join(DATA_DIR, "monje_millonario.csv"),
        "total_animals": 77,
        "payout": 60.0,
        "emoji": "🧘‍♂️"
    },
    "Granja Millonaria - Animalitos": {
        "file": os.path.join(DATA_DIR, "granja_millonaria_animalitos.csv"),
        "total_animals": 38,
        "payout": 30.0,
        "emoji": "🚜"
    },
    "Granja Millonaria - Granjazo": {
        "file": os.path.join(DATA_DIR, "granja_millonaria_granjazo.csv"),
        "total_animals": 68,
        "payout": 60.0,
        "emoji": "🌽"
    }
}

def analyze_roulette(name: str, meta: dict):
    filepath = meta["file"]
    if not os.path.exists(filepath):
        print(f"[!] Archivo no encontrado: {filepath}")
        return None

    df = pd.read_csv(filepath, dtype={"numero": str})
    df["numero"] = df["numero"].astype(str).str.strip()
    df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
    df = df.sort_values(by="sort_dt").reset_index(drop=True)
    nums = df["numero"].tolist()
    total_sorteos = len(nums)

    n_animals = meta["total_animals"]
    payout = meta["payout"]
    be_rate = (1.0 / payout) * 100.0
    random_prob = (1.0 / n_animals) * 100.0

    if total_sorteos < 100:
        return {
            "name": name,
            "status": "Muestra Insuficiente (<100 sorteos)",
            "sorteos": total_sorteos
        }

    # 1. Escaneo de Lags individuales (1 al 40)
    lag_scores = []
    max_scan_lag = min(40, total_sorteos - 50)

    for l in range(1, max_scan_lag + 1):
        trials = 0
        hits = 0
        for i in range(max(l, 6) + 1, total_sorteos):
            actual = nums[i]
            rec6 = set(nums[i-6:i])
            cand = nums[i-l]
            if cand not in rec6:
                trials += 1
                if actual == cand:
                    hits += 1
        if trials > 0:
            wr = (hits / trials * 100.0)
            edge_over_random = (wr / random_prob - 1.0) * 100.0
            lag_scores.append({
                "lag": l,
                "trials": trials,
                "hits": hits,
                "wr": wr,
                "edge": edge_over_random
            })

    df_lags = pd.DataFrame(lag_scores).sort_values(by="wr", ascending=False)
    
    # Seleccionar los mejores 2 a 4 lags (sin repetir horas redundantes)
    top_lags = df_lags.head(8)["lag"].tolist()
    
    # Filtrar para seleccionar 2 o 3 lags complementarios
    chosen_lags = []
    for l in top_lags:
        if len(chosen_lags) >= 3:
            break
        # evitar lags adyacentes inmediatos (ej l y l+1)
        if not any(abs(l - cl) <= 1 for cl in chosen_lags):
            chosen_lags.append(l)

    if not chosen_lags:
        chosen_lags = top_lags[:2]

    # 2. Evaluación de Rebote Sniper con los Lags Seleccionados
    max_l = max(chosen_lags)
    streak = 0
    sniper_trials = 0
    sniper_hits = 0
    sniper_animals_count = 0
    
    base_trials = 0
    base_hits = 0
    base_animals_count = 0
    
    # Historial de rachas
    streak_hits = {0: 0, 1: 0, 2: 0, 3: 0, "4+": 0}
    streak_trials = {0: 0, 1: 0, 2: 0, 3: 0, "4+": 0}

    for i in range(max_l + 7, total_sorteos):
        actual = nums[i]
        rec6 = set(nums[i-6:i])
        cands = list({nums[i-l] for l in chosen_lags} - rec6)
        
        if cands:
            cost = len(cands)
            hit = (actual in cands)
            base_trials += 1
            base_animals_count += cost
            if hit:
                base_hits += 1
                
            st_key = streak if streak in [0, 1, 2, 3] else "4+"
            streak_trials[st_key] += 1
            if hit:
                streak_hits[st_key] += 1

            if streak == 1:
                sniper_trials += 1
                sniper_animals_count += cost
                if hit:
                    sniper_hits += 1

            if hit:
                streak = 0
            else:
                streak += 1

    # Cálculos financieros a $1 fijo por animal
    base_wr = (base_hits / base_trials * 100.0) if base_trials > 0 else 0.0
    sniper_wr = (sniper_hits / sniper_trials * 100.0) if sniper_trials > 0 else 0.0
    
    sniper_inv = sniper_animals_count * 1.0 # $1 por animal
    sniper_cob = sniper_hits * payout * 1.0
    sniper_pnl = sniper_cob - sniper_inv
    sniper_roi = (sniper_pnl / sniper_inv * 100.0) if sniper_inv > 0 else 0.0

    # Probabilidad en racha 0 vs racha 1 vs racha 2
    wr_r0 = (streak_hits[0] / streak_trials[0] * 100.0) if streak_trials[0] > 0 else 0.0
    wr_r1 = (streak_hits[1] / streak_trials[1] * 100.0) if streak_trials[1] > 0 else 0.0
    wr_r2 = (streak_hits[2] / streak_trials[2] * 100.0) if streak_trials[2] > 0 else 0.0

    # Veredicto de constancia del patrón
    tiene_rebote = (wr_r1 > base_wr)
    es_rentable = (sniper_pnl > 0)
    supera_be = (sniper_wr > be_rate)

    if total_sorteos >= 1000 and es_rentable and tiene_rebote:
        veredicto = "🟢 VIABLE / PATRÓN SÓLIDO (+EV Confirmado)"
    elif total_sorteos < 1000 and es_rentable:
        veredicto = "🟡 PROMETEDOR (+EV en muestra corta, monitorear)"
    elif es_rentable:
        veredicto = "🟡 RENTABLE (+EV leve, optimizable)"
    else:
        veredicto = "🔴 NO RECOMENDADO (-EV, sin ventaja suficiente)"

    return {
        "name": name,
        "emoji": meta["emoji"],
        "total_sorteos": total_sorteos,
        "n_animals": n_animals,
        "payout": payout,
        "be_rate": be_rate,
        "random_prob": random_prob,
        "chosen_lags": chosen_lags,
        "top_lags_df": df_lags.head(5),
        "base_wr": base_wr,
        "sniper_trials": sniper_trials,
        "sniper_hits": sniper_hits,
        "sniper_loss": sniper_trials - sniper_hits,
        "sniper_wr": sniper_wr,
        "sniper_animals": sniper_animals_count,
        "prom_cands": (sniper_animals_count / sniper_trials) if sniper_trials > 0 else 0,
        "sniper_inv": sniper_inv,
        "sniper_cob": sniper_cob,
        "sniper_pnl": sniper_pnl,
        "sniper_roi": sniper_roi,
        "wr_r0": wr_r0,
        "wr_r1": wr_r1,
        "wr_r2": wr_r2,
        "tiene_rebote": tiene_rebote,
        "veredicto": veredicto
    }

def run_all():
    print("=" * 105)
    print(" 🔬 INFORME TÉCNICO: ANÁLISIS DE PATRONES DE REPETICIÓN Y GATILLO SNIPER")
    print("=" * 105)

    results = []
    for name, meta in CONFIG.items():
        res = analyze_roulette(name, meta)
        if res:
            results.append(res)

    print("\n" + "=" * 105)
    print(" 📋 TABLA COMPARATIVA GENERAL DE LAS NUEVAS RULETAS (APUESTA FIJA $1 POR ANIMAL)")
    print("=" * 105)
    print(f" {'Ruleta':<32} | {'Payout':<6} | {'Sorteos':<7} | {'Lags Óptimos':<14} | {'Win Rate Base':<14} | {'WR Racha 1':<12} | {'Break-Even':<10} | {'PnL ($1)':<12} | {'ROI Neto':<9} | {'Diagnóstico'}")
    print("-" * 145)

    for r in results:
        lags_str = str(r["chosen_lags"])
        pnl_str = f"{'+' if r['sniper_pnl']>=0 else ''}${r['sniper_pnl']:,.2f}"
        roi_str = f"{r['sniper_roi']:+.1f}%"
        print(f" {r['emoji']} {r['name']:<28} | {r['payout']:>4.0f}x | {r['total_sorteos']:>7,} | {lags_str:<14} | {r['base_wr']:>11.2f}% | {r['sniper_wr']:>9.2f}% | {r['be_rate']:>8.2f}% | {pnl_str:>12} | {roi_str:>9} | {r['veredicto']}")

    print("=" * 145 + "\n")

    # Detalle por ruleta
    for r in results:
        print("=" * 95)
        print(f" {r['emoji']} DETALLE TÉCNICO: {r['name'].upper()}")
        print("=" * 95)
        print(f" - Universo de Animales:     {r['n_animals']} figuras | Multiplicador de Pago: {r['payout']:.0f}x")
        print(f" - Probabilidad Aleatoria:   {r['random_prob']:.2f}% | Umbral Break-Even (1/Payout): {r['be_rate']:.2f}%")
        print(f" - Total Sorteos Analizados: {r['total_sorteos']:,}")
        print(f" - Lags Óptimos Detectados:  {r['chosen_lags']}")
        print(f" - Top 5 Lags con Mayor Autocorrelación:")
        for _, lrow in r["top_lags_df"].iterrows():
            print(f"     * Lag {int(lrow['lag']):>2}: {lrow['wr']:.2f}% WR ({int(lrow['hits'])}/{int(lrow['trials'])}) -> Ventaja vs Azar: {lrow['edge']:+.1f}%")
        print()
        print(f" - Dinámica de Rachas y Rebote:")
        print(f"     * WR Inmediato tras Acierto (Racha 0): {r['wr_r0']:.2f}%")
        print(f"     * 🎯 WR REBOTE TRAS 1 FALLO (Racha 1):  {r['wr_r1']:.2f}%  {'🔥 ¡Rebote Activo!' if r['wr_r1']>r['base_wr'] else '⚠️ Sin rebote claro'}")
        print(f"     * WR tras 2 Fallos Seguidos (Racha 2): {r['wr_r2']:.2f}%")
        print()
        print(f" - Simulación Financiera a $1.00 USD por Animal:")
        print(f"     * Sorteos donde Invertiría: {r['sniper_trials']} sorteos ({r['sniper_hits']} ganadas, {r['sniper_loss']} perdidas)")
        print(f"     * Total Fichas Apostadas:   {r['sniper_animals']} animales (promedio {r['prom_cands']:.2f} por sorteo)")
        print(f"     * Inversión Total:          ${r['sniper_inv']:,.2f} USD")
        print(f"     * Cobrado Total:            ${r['sniper_cob']:,.2f} USD")
        print(f"     * Beneficio Neto (PnL):     {'+' if r['sniper_pnl']>=0 else ''}${r['sniper_pnl']:,.2f} USD")
        print(f"     * Rentabilidad Neta (ROI):  {r['sniper_roi']:+.2f}%")
        print(f" - Veredicto: {r['veredicto']}")
        print()

if __name__ == "__main__":
    run_all()
