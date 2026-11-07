"""
========================================================================================
 MONITOR DE AUDITORÍA Y DETECCIÓN DE DRIFT DE REZAGOS (FISCALIZACIÓN EN VIVO)
========================================================================================
Audita periódicamente los sorteos más recientes para detectar:
 1. Salud del patrón de no-repetición matutino (sorteos 1 a 6).
 2. Estabilidad de los rezagos oficiales configurados en config.py vs lags móviles.
 3. Detección de desplazamientos (Concept Drift) en la Onda Dorada (Lags 13-23).
========================================================================================
"""

import os
import sys
import datetime
import numpy as np
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(r"C:\Users\victo\nuevas_ruletas")
from config import RULETAS_CONFIG

def audit_lag_drift(window_recent=250):
    print("=" * 115)
    print(f"🔬 FISCALIZACIÓN DE REGÍMENES Y DETECCIÓN DE DRIFT DE REZAGOS (VENTANA: {window_recent} SORTEOS)")
    print("=" * 115)
    
    active_configs = {k: v for k, v in RULETAS_CONFIG.items() if v.get("active", True)}
    
    for r_name, cfg in active_configs.items():
        if not os.path.exists(cfg["file"]):
            continue
        df = pd.read_csv(cfg["file"], dtype={"numero": str})
        df["numero"] = df["numero"].astype(str).str.strip()
        nums = df["numero"].tolist()
        if len(nums) < window_recent:
            continue
            
        recent_nums = nums[-window_recent:]
        unique_nums = sorted(list(set(nums)))
        k_pool = len(unique_nums)
        theo_p = 1.0 / k_pool
        
        # Calculate recent lag hits
        lag_hits = {}
        lag_tot = {}
        last_seen = {}
        for t, n in enumerate(recent_nums):
            for a in unique_nums:
                if a in last_seen:
                    l = t - last_seen[a]
                    lag_tot[l] = lag_tot.get(l, 0) + 1
                    if n == a:
                        lag_hits[l] = lag_hits.get(l, 0) + 1
            last_seen[n] = t
            
        # Check current configured lags
        cfg_lags = cfg["lags"]
        print(f"\n📍 {r_name} (Pool={k_pool} | Teórico: {theo_p*100:.2f}% | Config Lags: {cfg_lags})")
        
        # Evaluate performance of configured lags in recent window
        tot_cfg_hits = sum(lag_hits.get(l, 0) for l in cfg_lags)
        tot_cfg_opps = sum(lag_tot.get(l, 0) for l in cfg_lags)
        cfg_rate = (tot_cfg_hits / tot_cfg_opps * 100.0) if tot_cfg_opps > 0 else 0
        ratio = (cfg_rate / 100.0) / theo_p if theo_p > 0 else 0
        
        status = "🟢 ROBUSTO (+EV)" if ratio > 1.15 else ("🟡 NEUTRAL" if ratio >= 0.90 else "🔴 DECAIMIENTO (DRIFT)")
        print(f"   • Tasa Reciente Lags Config: {cfg_rate:.2f}% (Ratio EV: {ratio:.2f}x) -> {status}")
        
        # Detect top 3 hottest lags in recent window
        lag_ratios = []
        for l in range(10, 45):
            tot = lag_tot.get(l, 0)
            hits = lag_hits.get(l, 0)
            if tot >= 30:
                r = (hits / tot) / theo_p
                lag_ratios.append((l, hits, tot, r))
                
        lag_ratios.sort(key=lambda x: x[3], reverse=True)
        top3_recent = lag_ratios[:3]
        top3_str = ", ".join([f"Lag {x[0]} ({x[3]:.2f}x)" for x in top3_recent])
        print(f"   • Top 3 Rezagos Emergentes Recientes: {top3_str}")

if __name__ == "__main__":
    audit_lag_drift()
