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

def run_comparison_15d_vs_30d():
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
        
    print(f"Total eventos cargados: {len(all_events):,}")
    print(f"Rango: {all_events[0]['dt']} -> {all_events[-1]['dt']}")
    
    results = {}
    
    for window_days in [30, 15]:
        print(f"\n{'='*70}\nPROCESANDO VENTANA MÓVIL DE {window_days} DÍAS\n{'='*70}")
        annotated_events = []
        for i, ev in enumerate(all_events):
            t = ev["dt"]
            t_win = t - timedelta(days=window_days)
            
            perf = {}
            for r_name, r_evs in events_by_r.items():
                recent = [e for e in r_evs if t_win <= e["dt"] < t]
                if recent:
                    perf[r_name] = sum(e["payout"] if e["hit"] else 0 - e["total_cands"] for e in recent)
                else:
                    if r_evs[0]["dt"] <= t <= r_evs[-1]["dt"]:
                        perf[r_name] = 0.0
                        
            sorted_ruletas = sorted(perf.items(), key=lambda x: x[1], reverse=True)
            cur_r = ev["ruleta"]
            rank = 1
            for rk, (rc, _) in enumerate(sorted_ruletas, 1):
                if rc == cur_r:
                    rank = rk
                    break
                    
            if rank <= 3:
                color, stake = "VERDE", 1.50
            elif rank <= 5:
                color, stake = "AMARILLO", 1.00
            else:
                color, stake = "ROJO", 0.50
                
            e_copy = dict(ev)
            e_copy["color"] = color
            e_copy["stake_unit"] = stake
            e_copy["rank"] = rank
            annotated_events.append(e_copy)
            
        # Standalone breakdown by color
        print(f"\n--- AUDITORÍA AISLADA POR COLOR ({window_days} DÍAS) ---")
        for col in ["VERDE", "AMARILLO", "ROJO"]:
            sub = [e for e in annotated_events if e["color"] == col]
            b = len(sub)
            w = sum(1 for e in sub if e["hit"])
            wr = (w / b * 100) if b > 0 else 0
            inv = sum(e["stake_unit"] * e["total_cands"] for e in sub)
            cob = sum(e["stake_unit"] * e["payout"] for e in sub if e["hit"])
            pnl = cob - inv
            roi = (pnl / inv * 100) if inv > 0 else 0
            pf = (cob / inv) if inv > 0 else 0
            print(f"Color {col:8} (Stake ${sub[0]['stake_unit'] if sub else 0:.2f}): Disparos={b:5} | Aciertos={w:4} ({wr:5.2f}%) | Inv=${inv:10,.2f} | Cob=${cob:10,.2f} | PnL={'+' if pnl>=0 else ''}${pnl:9,.2f} | ROI={'+' if roi>=0 else ''}{roi:5.2f}% | PF={pf:.3f}")

        # The 3 Scenarios
        scenarios = [
            ("Escenario 1 (Todos los Colores)", ["VERDE", "AMARILLO", "ROJO"]),
            ("Escenario 2 (Verde y Amarillo)", ["VERDE", "AMARILLO"]),
            ("Escenario 3 (Solo Verde)", ["VERDE"])
        ]
        
        results[window_days] = {}
        for sc_name, allowed in scenarios:
            bets = 0
            wins = 0
            total_invested = 0.0
            total_returned = 0.0
            pnl_history = []
            running_pnl = 0.0
            peak_pnl = 0.0
            max_dd = 0.0
            monthly_pnl = {}
            
            for ev in annotated_events:
                if ev["color"] not in allowed:
                    continue
                stk = ev["stake_unit"]
                c_cost = round(stk * ev["total_cands"], 2)
                c_won = round(stk * ev["payout"], 2) if ev["hit"] else 0.0
                pnl = round(c_won - c_cost, 2)
                
                bets += 1
                if ev["hit"]:
                    wins += 1
                total_invested += c_cost
                total_returned += c_won
                running_pnl += pnl
                pnl_history.append(running_pnl)
                
                if running_pnl > peak_pnl:
                    peak_pnl = running_pnl
                dd = peak_pnl - running_pnl
                if dd > max_dd:
                    max_dd = dd
                    
                m_key = str(ev["fecha"])[:7]
                monthly_pnl[m_key] = monthly_pnl.get(m_key, 0.0) + pnl
                
            net_pnl = total_returned - total_invested
            roi = (net_pnl / total_invested * 100.0) if total_invested > 0 else 0.0
            wr = (wins / bets * 100.0) if bets > 0 else 0.0
            pf = (total_returned / total_invested) if total_invested > 0 else 0.0
            m_vals = list(monthly_pnl.values())
            pos_m = sum(1 for v in m_vals if v > 0)
            tot_m = len(m_vals)
            sharpe = (np.mean(m_vals) / np.std(m_vals) * np.sqrt(12)) if len(m_vals) > 1 and np.std(m_vals) > 0 else 0.0
            
            results[window_days][sc_name] = {
                "bets": bets, "wins": wins, "wr": wr,
                "invested": total_invested, "returned": total_returned,
                "pnl": net_pnl, "roi": roi, "pf": pf,
                "max_dd": max_dd, "pos_m": pos_m, "tot_m": tot_m, "sharpe": sharpe
            }
            
    print("\n" + "#" * 80)
    print("MATRIZ COMPARATIVA DIRECTA: 30 DÍAS VS 15 DÍAS")
    print("#" * 80)
    for sc_name in ["Escenario 1 (Todos los Colores)", "Escenario 2 (Verde y Amarillo)", "Escenario 3 (Solo Verde)"]:
        r30 = results[30][sc_name]
        r15 = results[15][sc_name]
        diff_pnl = r15["pnl"] - r30["pnl"]
        diff_roi = r15["roi"] - r30["roi"]
        diff_dd = r15["max_dd"] - r30["max_dd"]
        print(f"\n>>> {sc_name.upper()} <<<")
        print(f"  • Disparos:       30d = {r30['bets']:,} (WR {r30['wr']:.2f}%)  |  15d = {r15['bets']:,} (WR {r15['wr']:.2f}%)")
        print(f"  • Inversión:      30d = ${r30['invested']:,.2f} USD  |  15d = ${r15['invested']:,.2f} USD")
        print(f"  • Cobrado:        30d = ${r30['returned']:,.2f} USD  |  15d = ${r15['returned']:,.2f} USD")
        print(f"  • Ganancia Neta:  30d = +${r30['pnl']:,.2f} USD  |  15d = +${r15['pnl']:,.2f} USD  (Diferencia: {'+' if diff_pnl>=0 else ''}${diff_pnl:,.2f} USD)")
        print(f"  • ROI:            30d = +{r30['roi']:.2f}%  |  15d = +{r15['roi']:.2f}%  (Diferencia: {'+' if diff_roi>=0 else ''}{diff_roi:+.2f}%)")
        print(f"  • Profit Factor:  30d = {r30['pf']:.3f}  |  15d = {r15['pf']:.3f}")
        print(f"  • Max Drawdown:   30d = -${r30['max_dd']:,.2f} USD  |  15d = -${r15['max_dd']:,.2f} USD  (Diferencia: {'+' if diff_dd>=0 else ''}${diff_dd:,.2f} USD)")
        print(f"  • Sharpe Anual:   30d = {r30['sharpe']:.2f}  |  15d = {r15['sharpe']:.2f}")

run_comparison_15d_vs_30d()
