"""
========================================================================================
 ANÁLISIS BIDIMENSIONAL: FILAS (HORAS) VS COLUMNAS (DÍAS)
========================================================================================
Organiza la secuencia histórica en una matriz 2D:
 - Filas = Horas del sorteo (ej. 8:00 AM, 9:00 AM, 10:00 AM...)
 - Columnas = Fechas / Días consecutivos

Evalúa:
 1. Patrón en FILAS (Intra-día / Secuencia horaria continua):
    - ¿Cómo se comporta la repetición de hora a hora dentro del mismo día?
    - ¿Qué tasa de acierto y rebote genera?
 2. Patrón en COLUMNAS (Inter-día / Misma hora día tras día):
    - ¿Cómo se comporta la repetición de día a día para la MISMA hora fija?
      * Día -1 (ayer a la misma hora)
      * Día -2 (antier a la misma hora)
      * Día -3 (hace 3 días a la misma hora)
      * Día -7 (mismo día de la semana anterior a la misma hora)
    - ¿Existe efecto rebote Post-Fallo 1 cuando se opera exclusivamente columna a columna?
 3. Comparación Directa: ¿El patrón es puramente horario (filas), puramente diario (columnas),
    o es una combinación tridimensional?
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
    "Lotto Gato": {
        "file": os.path.join(DATA_DIR, "lotto_gato.csv"),
        "total_animals": 47,
        "payout": 30.0,
        "emoji": "🐱"
    },
    "Monje Millonario": {
        "file": os.path.join(DATA_DIR, "monje_millonario.csv"),
        "total_animals": 77,
        "payout": 60.0,
        "emoji": "🧘‍♂️"
    },
    "Lotto Activo (Referencia)": {
        "file": r"C:\Users\victo\.gemini\antigravity\scratch\lotto_activo_bot\lotto_activo_2anios.csv",
        "total_animals": 38,
        "payout": 30.0,
        "emoji": "🦁"
    }
}

def analyze_matrix_dimensions(name: str, meta: dict):
    filepath = meta["file"]
    if not os.path.exists(filepath):
        return None

    df = pd.read_csv(filepath, dtype={"numero": str})
    df["numero"] = df["numero"].astype(str).str.strip()
    df["_h"] = pd.to_datetime(df["hora"], format="%I:%M %p", errors="coerce").dt.time
    df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
    df = df.sort_values(by="sort_dt").reset_index(drop=True)

    n_animals = meta["total_animals"]
    payout = meta["payout"]
    be_rate = (1.0 / payout) * 100.0
    random_prob = (1.0 / n_animals) * 100.0

    # Crear Matriz Pivot: Filas = Horas ordenadas, Columnas = Fechas ordenadas
    horas_ordenadas = sorted(df["hora"].dropna().unique(), key=lambda h: pd.to_datetime(h, format="%I:%M %p", errors="coerce").time())
    fechas_ordenadas = sorted(df["fecha"].dropna().unique())

    # Pivot table con números
    pivot = df.pivot(index="hora", columns="fecha", values="numero")
    # Reindexar horas en orden cronológico del día
    pivot = pivot.reindex(horas_ordenadas)

    # ---------------------------------------------------------
    # 1. ANÁLISIS EN COLUMNAS (Misma hora fija, a través de los días)
    # Para cada hora h, comparamos el valor de la fecha d con d-1, d-2, d-3, d-7
    # ---------------------------------------------------------
    col_lags_results = {1: {"trials": 0, "hits": 0}, 2: {"trials": 0, "hits": 0}, 3: {"trials": 0, "hits": 0}, 7: {"trials": 0, "hits": 0}}

    for lag_days in [1, 2, 3, 7]:
        for h in horas_ordenadas:
            if h not in pivot.index:
                continue
            row_vals = pivot.loc[h].tolist()
            for col_idx in range(lag_days, len(row_vals)):
                val_today = row_vals[col_idx]
                val_past = row_vals[col_idx - lag_days]
                if pd.notna(val_today) and pd.notna(val_past) and str(val_today) != "-" and str(val_past) != "-":
                    col_lags_results[lag_days]["trials"] += 1
                    if str(val_today).strip() == str(val_past).strip():
                        col_lags_results[lag_days]["hits"] += 1

    # Evaluación de rebote EN COLUMNAS (Siguiendo la racha día a día en la misma hora)
    # Estrategia: mirar la misma hora, si ayer falló (racha=1 en esa hora), ¿rebota hoy?
    col_streak_trials = {0: 0, 1: 0, 2: 0}
    col_streak_hits = {0: 0, 1: 0, 2: 0}
    
    # Para la prueba combinando ayer (d-1) y anteayer (d-2) en la misma hora
    col_sniper_trials = 0
    col_sniper_hits = 0
    col_sniper_animals = 0

    for h in horas_ordenadas:
        if h not in pivot.index:
            continue
        row_vals = pivot.loc[h].tolist()
        streak = 0
        for col_idx in range(3, len(row_vals)):
            val_today = row_vals[col_idx]
            cand1 = row_vals[col_idx - 1]
            cand2 = row_vals[col_idx - 2]
            
            cands = set()
            if pd.notna(cand1) and str(cand1) != "-": cands.add(str(cand1).strip())
            if pd.notna(cand2) and str(cand2) != "-": cands.add(str(cand2).strip())
            
            if pd.notna(val_today) and str(val_today) != "-" and cands:
                val_str = str(val_today).strip()
                hit = (val_str in cands)
                
                if streak in [0, 1, 2]:
                    col_streak_trials[streak] += 1
                    if hit: col_streak_hits[streak] += 1
                
                if streak == 1:
                    col_sniper_trials += 1
                    col_sniper_animals += len(cands)
                    if hit: col_sniper_hits += 1
                    
                if hit: streak = 0
                else: streak += 1

    # ---------------------------------------------------------
    # 2. ANÁLISIS EN FILAS (Intra-día: horas consecutivas dentro del mismo día)
    # Para cada fecha d fija, comparamos hora i con hora i-1, i-2, i-3
    # ---------------------------------------------------------
    row_lags_results = {1: {"trials": 0, "hits": 0}, 2: {"trials": 0, "hits": 0}, 3: {"trials": 0, "hits": 0}}
    
    for lag_hours in [1, 2, 3]:
        for f in fechas_ordenadas:
            if f not in pivot.columns:
                continue
            col_vals = pivot[f].tolist()
            for row_idx in range(lag_hours, len(col_vals)):
                val_cur = col_vals[row_idx]
                val_prev = col_vals[row_idx - lag_hours]
                if pd.notna(val_cur) and pd.notna(val_prev) and str(val_cur) != "-" and str(val_prev) != "-":
                    row_lags_results[lag_hours]["trials"] += 1
                    if str(val_cur).strip() == str(val_prev).strip():
                        row_lags_results[lag_hours]["hits"] += 1

    # ---------------------------------------------------------
    # Cálculos finales
    # ---------------------------------------------------------
    col_lag1_wr = (col_lags_results[1]["hits"] / col_lags_results[1]["trials"] * 100.0) if col_lags_results[1]["trials"] > 0 else 0
    col_lag2_wr = (col_lags_results[2]["hits"] / col_lags_results[2]["trials"] * 100.0) if col_lags_results[2]["trials"] > 0 else 0
    col_lag3_wr = (col_lags_results[3]["hits"] / col_lags_results[3]["trials"] * 100.0) if col_lags_results[3]["trials"] > 0 else 0
    col_lag7_wr = (col_lags_results[7]["hits"] / col_lags_results[7]["trials"] * 100.0) if col_lags_results[7]["trials"] > 0 else 0

    row_lag1_wr = (row_lags_results[1]["hits"] / row_lags_results[1]["trials"] * 100.0) if row_lags_results[1]["trials"] > 0 else 0
    row_lag2_wr = (row_lags_results[2]["hits"] / row_lags_results[2]["trials"] * 100.0) if row_lags_results[2]["trials"] > 0 else 0
    row_lag3_wr = (row_lags_results[3]["hits"] / row_lags_results[3]["trials"] * 100.0) if row_lags_results[3]["trials"] > 0 else 0

    col_sniper_wr = (col_sniper_hits / col_sniper_trials * 100.0) if col_sniper_trials > 0 else 0
    col_sniper_inv = col_sniper_animals * 1.0
    col_sniper_cob = col_sniper_hits * payout * 1.0
    col_sniper_pnl = col_sniper_cob - col_sniper_inv
    col_sniper_roi = (col_sniper_pnl / col_sniper_inv * 100.0) if col_sniper_inv > 0 else 0

    col_wr_r0 = (col_streak_hits[0] / col_streak_trials[0] * 100.0) if col_streak_trials[0] > 0 else 0
    col_wr_r1 = (col_streak_hits[1] / col_streak_trials[1] * 100.0) if col_streak_trials[1] > 0 else 0
    col_wr_r2 = (col_streak_hits[2] / col_streak_trials[2] * 100.0) if col_streak_trials[2] > 0 else 0

    return {
        "name": name,
        "emoji": meta["emoji"],
        "n_animals": n_animals,
        "payout": payout,
        "be_rate": be_rate,
        "random_prob": random_prob,
        "total_sorteos": len(df),
        "total_dias": len(fechas_ordenadas),
        "horas_por_dia": len(horas_ordenadas),
        "pivot_shape": pivot.shape,
        # Filas (Intra-día)
        "row_lag1_wr": row_lag1_wr,
        "row_lag2_wr": row_lag2_wr,
        "row_lag3_wr": row_lag3_wr,
        # Columnas (Inter-día)
        "col_lag1_wr": col_lag1_wr,
        "col_lag2_wr": col_lag2_wr,
        "col_lag3_wr": col_lag3_wr,
        "col_lag7_wr": col_lag7_wr,
        # Rebote en columnas
        "col_wr_r0": col_wr_r0,
        "col_wr_r1": col_wr_r1,
        "col_wr_r2": col_wr_r2,
        "col_sniper_trials": col_sniper_trials,
        "col_sniper_hits": col_sniper_hits,
        "col_sniper_wr": col_sniper_wr,
        "col_sniper_inv": col_sniper_inv,
        "col_sniper_cob": col_sniper_cob,
        "col_sniper_pnl": col_sniper_pnl,
        "col_sniper_roi": col_sniper_roi
    }

def run():
    print("=" * 105)
    print(" 🧭 ANÁLISIS COMPARATIVO MATRICIAL: FILAS (HORAS) VS COLUMNAS (DÍAS)")
    print("=" * 105)

    for name, meta in CONFIG.items():
        res = analyze_matrix_dimensions(name, meta)
        if not res:
            continue

        print(f"\n{'='*95}")
        print(f" {res['emoji']} {res['name'].upper()} | Tablero: {res['horas_por_dia']} Horas (Filas) x {res['total_dias']} Días (Columnas)")
        print(f"    Total Sorteos: {res['total_sorteos']:,} | Azar Teórico: {res['random_prob']:.2f}% | Break-Even: {res['be_rate']:.2f}% (Payout {res['payout']:.0f}x)")
        print(f"{'='*95}")

        print("\n 1️⃣ ANÁLISIS EN FILAS (MOVIMIENTO INTRA-DÍA / HORA TRAS HORA):")
        print(f"   - Repetición Hora Inmediata Anterior (Lag 1 hora):   {res['row_lag1_wr']:.2f}%  (Ventaja vs Azar: {(res['row_lag1_wr']/res['random_prob']-1)*100:+.1f}%)")
        print(f"   - Repetición de Hace 2 Horas (Lag 2 horas):          {res['row_lag2_wr']:.2f}%  (Ventaja vs Azar: {(res['row_lag2_wr']/res['random_prob']-1)*100:+.1f}%)")
        print(f"   - Repetición de Hace 3 Horas (Lag 3 horas):          {res['row_lag3_wr']:.2f}%  (Ventaja vs Azar: {(res['row_lag3_wr']/res['random_prob']-1)*100:+.1f}%)")
        print("   -> Diagnóstico Filas: La repetición inmediata hora a hora (Lag 1h) es muy baja por la regla de no-repetición continua.")

        print("\n 2️⃣ ANÁLISIS EN COLUMNAS (MOVIMIENTO INTER-DÍA / MISMA HORA A TRAVÉS DE LOS DÍAS):")
        print(f"   - Misma Hora Ayer (Día -1):                          {res['col_lag1_wr']:.2f}%  (Ventaja vs Azar: {(res['col_lag1_wr']/res['random_prob']-1)*100:+.1f}%)")
        print(f"   - Misma Hora Antier (Día -2):                        {res['col_lag2_wr']:.2f}%  (Ventaja vs Azar: {(res['col_lag2_wr']/res['random_prob']-1)*100:+.1f}%)")
        print(f"   - Misma Hora Hace 3 Días (Día -3):                   {res['col_lag3_wr']:.2f}%  (Ventaja vs Azar: {(res['col_lag3_wr']/res['random_prob']-1)*100:+.1f}%)")
        print(f"   - Mismo Día Semana Pasada (Día -7):                  {res['col_lag7_wr']:.2f}%  (Ventaja vs Azar: {(res['col_lag7_wr']/res['random_prob']-1)*100:+.1f}%)")

        print("\n 3️⃣ ¿SE REPLICA EL PATRÓN DE REBOTE SNIPER EN LAS COLUMNAS? (Operando columna por columna):")
        print(f"   - Tasa tras Acierto en la misma hora (Racha 0):      {res['col_wr_r0']:.2f}%")
        print(f"   - 🎯 TASA TRAS 1 FALLO EN LA MISMA HORA (Racha 1):    {res['col_wr_r1']:.2f}%  {'🔥 ¡Rebote Confirmado en Columnas!' if res['col_wr_r1']>res['col_wr_r0'] else '⚠️ Sin rebote en columnas'}")
        print(f"   - Tasa tras 2 Fallos en la misma hora (Racha 2):     {res['col_wr_r2']:.2f}%")
        print(f"   - Simulación Sniper en Columnas ($1 fijo por animal):")
        print(f"     * Disparos: {res['col_sniper_trials']} | Aciertos: {res['col_sniper_hits']} ({res['col_sniper_wr']:.2f}% WR)")
        print(f"     * Invertido: ${res['col_sniper_inv']:,.2f} | Cobrado: ${res['col_sniper_cob']:,.2f} | PnL: {'+' if res['col_sniper_pnl']>=0 else ''}${res['col_sniper_pnl']:,.2f} ({res['col_sniper_roi']:+.1f}% ROI)")

if __name__ == "__main__":
    run()
