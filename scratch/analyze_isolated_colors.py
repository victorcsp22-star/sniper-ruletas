import os
import sys
import pandas as pd
import numpy as np
from datetime import timedelta

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(r"C:\Users\victo\nuevas_ruletas")
from config import RULETAS_CONFIG
from test_event_extractor import extract_roulette_events

all_events = []
for r_name, cfg in RULETAS_CONFIG.items():
    if not cfg.get("active", False):
        continue
    evs = extract_roulette_events(r_name, cfg)
    all_events.extend(evs)
all_events.sort(key=lambda x: x["dt"])

events_by_r = {}
for ev in all_events:
    events_by_r.setdefault(ev["ruleta"], []).append(ev)

def analyze_tier_standalone(is_quantile=False, year_filter=None):
    annotated = []
    for ev in all_events:
        t = ev["dt"]
        if year_filter and str(ev["fecha"])[:4] != str(year_filter):
            continue
        t_30d = t - timedelta(days=30)
        perf_30d = {}
        for r_name, r_evs in events_by_r.items():
            recent = [e for e in r_evs if t_30d <= e["dt"] < t]
            if recent:
                perf_30d[r_name] = sum(e["payout"] if e["hit"] else 0 - e["total_cands"] for e in recent)
            else:
                if r_evs[0]["dt"] <= t <= r_evs[-1]["dt"]:
                    perf_30d[r_name] = 0.0
                    
        sorted_ruletas = sorted(perf_30d.items(), key=lambda x: x[1], reverse=True)
        n_active = len(sorted_ruletas)
        cur_r = ev["ruleta"]
        rank = 1
        for rk, (rc, _) in enumerate(sorted_ruletas, 1):
            if rc == cur_r:
                rank = rk
                break
                
        if not is_quantile:
            if rank <= 3: color, stake = "VERDE", 1.50
            elif rank <= 5: color, stake = "AMARILLO", 1.00
            else: color, stake = "ROJO", 0.50
        else:
            if n_active <= 2:
                color, stake = ("VERDE", 1.50) if rank == 1 else ("AMARILLO", 1.00)
            elif n_active <= 4:
                if rank == 1: color, stake = "VERDE", 1.50
                elif rank == 2: color, stake = "AMARILLO", 1.00
                else: color, stake = "ROJO", 0.50
            else:
                v_cut = max(1, round(n_active * 0.375))
                a_cut = max(v_cut + 1, round(n_active * 0.625))
                if rank <= v_cut: color, stake = "VERDE", 1.50
                elif rank <= a_cut: color, stake = "AMARILLO", 1.00
                else: color, stake = "ROJO", 0.50
                
        e_copy = dict(ev)
        e_copy["color"] = color
        e_copy["stake_unit"] = stake
        annotated.append(e_copy)
        
    print(f"\n--- AUDITORÍA AISLADA POR COLOR (Filtro Año: {year_filter or '2 Años Completos'}) ---")
    for col in ["VERDE", "AMARILLO", "ROJO"]:
        sub = [e for e in annotated if e["color"] == col]
        b = len(sub)
        w = sum(1 for e in sub if e["hit"])
        wr = (w / b * 100) if b > 0 else 0
        inv = sum(e["stake_unit"] * e["total_cands"] for e in sub)
        cob = sum(e["stake_unit"] * e["payout"] for e in sub if e["hit"])
        pnl = cob - inv
        roi = (pnl / inv * 100) if inv > 0 else 0
        pf = (cob / inv) if inv > 0 else 0
        print(f"Color {col:8} (Stake ${sub[0]['stake_unit'] if sub else 0:.2f}): Disparos={b:5} | Aciertos={w:4} ({wr:5.2f}%) | Inv=${inv:10,.2f} | Cob=${cob:10,.2f} | PnL={'+' if pnl>=0 else ''}${pnl:9,.2f} | ROI={'+' if roi>=0 else ''}{roi:5.2f}% | PF={pf:.3f}")

analyze_tier_standalone(is_quantile=False)
analyze_tier_standalone(is_quantile=True)
analyze_tier_standalone(is_quantile=True, year_filter=2026)
