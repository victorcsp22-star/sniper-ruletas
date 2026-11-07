"""
========================================================================================
 ANÁLISIS DE LA CONDICIÓN ÓPTIMA DEL PATRÓN E INVERSIÓN INTELIGENTE (2 AÑOS)
========================================================================================
Examina en toda la historia disponible de las 7 ruletas:
 1. Condición por Tamaño de Canasta (Número de Animales Candidatos).
 2. Condición por Salud Dinámica del Patrón (Rolling Win Rate vs Break-Even).
 3. Condición por Racha de Fallos Consecutivos del Disparador (Circuit Breaker / Gatillo Virtual).
 4. Backtest Comparativo:
    - Estrategia Base (Full Kelly + Grossman-Zhou actual).
    - Inversión Inteligente con Priorización de Salud Dinámica.
    - Inversión Inteligente con Filtro de Condición Óptima.
========================================================================================
"""

import os
import sys
import numpy as np
import pandas as pd

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

VZ_DIR = r"C:\Users\victo\.gemini\antigravity\scratch\lotto_activo_bot"
NEW_DIR = r"C:\Users\victo\nuevas_ruletas"

RULETAS = {
    "Lotto Activo": {"file": os.path.join(VZ_DIR, "lotto_activo_2anios.csv"), "lags": [20, 18, 14], "payout": 30.0, "target_streaks": [1], "f_unit": 0.00900, "emoji": "🦁"},
    "La Granjita": {"file": os.path.join(VZ_DIR, "la_granjita_2anios.csv"), "lags": [15, 17], "payout": 30.0, "target_streaks": [1], "f_unit": 0.00484, "emoji": "🐸"},
    "Ruleta Royal": {"file": os.path.join(VZ_DIR, "ruleta_royal_2anios.csv"), "lags": [16, 19, 31], "payout": 30.0, "target_streaks": [1], "f_unit": 0.00826, "emoji": "👑"},
    "Guacharo Activo": {"file": os.path.join(VZ_DIR, "guacharo_activo_2anios.csv"), "lags": [31, 41, 25, 42, 35], "payout": 60.0, "target_streaks": [1], "f_unit": 0.00680, "emoji": "🦇"},
    "Gatazo": {"file": os.path.join(NEW_DIR, "gatazo.csv"), "lags": [35, 22, 20], "payout": 60.0, "target_streaks": [1, 2], "f_unit": 0.00900, "emoji": "🐯"},
    "Mega Animal 40": {"file": os.path.join(NEW_DIR, "mega_animal_40.csv"), "lags": [18, 21, 37], "payout": 30.0, "target_streaks": [1], "f_unit": 0.00800, "emoji": "🦏"},
    "Monje Millonario": {"file": os.path.join(NEW_DIR, "monje_millonario.csv"), "lags": [24, 35, 37], "payout": 60.0, "target_streaks": [1], "f_unit": 0.00700, "emoji": "🧘‍♂️"}
}

def extract_all_signals():
    all_signals = []
    
    for r_name, cfg in RULETAS.items():
        if not os.path.exists(cfg["file"]):
            continue
        df = pd.read_csv(cfg["file"], dtype={"numero": str})
        df["numero"] = df["numero"].astype(str).str.strip()
        df["dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        df = df.dropna(subset=["dt"]).sort_values("dt").reset_index(drop=True)
        
        nums = df["numero"].tolist()
        lags = cfg["lags"]
        payout = cfg["payout"]
        target_streaks = cfg["target_streaks"]
        f_unit = cfg["f_unit"]
        be_rate = (1.0 / payout) * 100.0
        min_idx = max(lags) + 6
        
        streak = 0
        r_history_hits = []
        
        for i in range(min_idx, len(nums)):
            actual = nums[i]
            rec6 = set(nums[i-6:i])
            cands = sorted(list({nums[i-l] for l in lags} - rec6))
            cost = len(cands)
            hit = (actual in cands)
            
            # Si el patrón da señal válida
            if streak in target_streaks and cost > 0:
                # Calcular salud del patrón previa a este disparo (últimos 15 disparos)
                w15 = r_history_hits[-15:] if len(r_history_hits) >= 15 else r_history_hits
                w15_hits = sum(w15)
                w15_wr = (w15_hits / len(w15) * 100.0) if len(w15) > 0 else be_rate
                health_ratio = w15_wr / be_rate
                
                # Racha de fallos consecutivos en el gatillo (consecutive trigger misses)
                # Contar cuántos fallos seguidos lleva este gatillo recientemente
                trig_misses = 0
                for h in reversed(r_history_hits):
                    if not h:
                        trig_misses += 1
                    else:
                        break
                
                all_signals.append({
                    "dt": df.iloc[i]["dt"],
                    "fecha": df.iloc[i]["fecha"],
                    "hora": df.iloc[i]["hora"],
                    "ruleta": r_name,
                    "emoji": cfg["emoji"],
                    "payout": payout,
                    "be_rate": be_rate,
                    "f_unit": f_unit,
                    "cands_count": cost,
                    "cands": cands,
                    "actual": actual,
                    "hit": hit,
                    "streak_at_entry": streak,
                    "health_ratio_w15": health_ratio,
                    "w15_wr": w15_wr,
                    "hist_signals_len": len(r_history_hits),
                    "trig_consec_misses": trig_misses
                })
                
                r_history_hits.append(hit)
                
            if hit:
                streak = 0
            else:
                streak += 1
                
    # Ordenar cronológicamente
    all_signals.sort(key=lambda x: x["dt"])
    return all_signals

def analyze_conditions():
    signals = extract_all_signals()
    df_sig = pd.DataFrame(signals)
    
    print("=" * 100)
    print(" 🔬 1. ESTUDIO POR TAMAÑO DE CANASTA (NÚMERO DE CANDIDATOS DEL PATRÓN)")
    print("=" * 100)
    
    basket_analysis = []
    for k, grp in df_sig.groupby("cands_count"):
        tot = len(grp)
        hits = grp["hit"].sum()
        wr = hits / tot * 100.0
        # ROI promedio normalizado por unidad apostada
        inv = (grp["cands_count"]).sum()
        cob = (grp["hit"] * grp["payout"]).sum()
        pnl = cob - inv
        roi = pnl / inv * 100.0
        basket_analysis.append({"fichas": k, "disparos": tot, "aciertos": hits, "win_rate": wr, "roi": roi, "pnl": pnl})
    
    df_basket = pd.DataFrame(basket_analysis)
    print(df_basket.to_string(index=False))
    
    print("\n" + "=" * 100)
    print(" 🔬 2. ESTUDIO POR SALUD DEL PATRÓN (ROLLING WIN RATE / BREAK-EVEN EN VENTANA DE 15 DISPAROS)")
    print("=" * 100)
    
    # Dividir en 3 estados de salud:
    # - ÓPTIMO (health_ratio >= 1.5): El patrón viene rindiendo a >1.5x su tasa de break-even.
    # - NEUTRAL (1.0 <= health_ratio < 1.5): En línea con break-even.
    # - DEGRADADO (health_ratio < 1.0): Racha fría por debajo de break-even.
    
    health_bins = [
        ("🟢 ESTADO ÓPTIMO (Health >= 1.5x BE)", df_sig[df_sig["health_ratio_w15"] >= 1.5]),
        ("🟡 ESTADO NEUTRAL (1.0x <= Health < 1.5x BE)", df_sig[(df_sig["health_ratio_w15"] >= 1.0) & (df_sig["health_ratio_w15"] < 1.5)]),
        ("🔴 ESTADO DEGRADADO (Health < 1.0x BE)", df_sig[df_sig["health_ratio_w15"] < 1.0])
    ]
    
    health_res = []
    for label, grp in health_bins:
        tot = len(grp)
        if tot == 0:
            continue
        hits = grp["hit"].sum()
        wr = hits / tot * 100.0
        inv = grp["cands_count"].sum()
        cob = (grp["hit"] * grp["payout"]).sum()
        pnl = cob - inv
        roi = pnl / inv * 100.0
        health_res.append({"Estado de Salud": label, "Disparos": tot, "Aciertos": hits, "Win Rate": f"{wr:.2f}%", "ROI Plano": f"{roi:+.2f}%", "PnL Plano ($)": pnl})
    
    df_hres = pd.DataFrame(health_res)
    print(df_hres.to_string(index=False))
    
    print("\n" + "=" * 100)
    print(" 🔬 3. ESTUDIO POR RACHA DE FALLOS CONSECUTIVOS DEL GATILLO")
    print("=" * 100)
    
    miss_res = []
    for m in range(0, 15):
        grp = df_sig[df_sig["trig_consec_misses"] == m]
        tot = len(grp)
        if tot >= 10:
            hits = grp["hit"].sum()
            wr = hits / tot * 100.0
            inv = grp["cands_count"].sum()
            cob = (grp["hit"] * grp["payout"]).sum()
            pnl = cob - inv
            roi = pnl / inv * 100.0
            miss_res.append({"Fallos Previos del Gatillo": m, "Disparos": tot, "Aciertos": hits, "Win Rate": f"{wr:.2f}%", "ROI Plano": f"{roi:+.2f}%"})
    
    df_miss = pd.DataFrame(miss_res)
    print(df_miss.to_string(index=False))

if __name__ == "__main__":
    analyze_conditions()
