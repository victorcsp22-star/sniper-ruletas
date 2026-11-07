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

def run_backtest_dynamic_colors():
    print("=" * 80)
    print("EJECUTANDO EXTRACCIÓN HISTÓRICA COMPLETA DE EVENTOS (2 AÑOS)...")
    print("=" * 80)
    
    all_events = []
    for r_name, cfg in RULETAS_CONFIG.items():
        if not cfg.get("active", False):
            continue
        evs = extract_roulette_events(r_name, cfg)
        all_events.extend(evs)
        
    all_events.sort(key=lambda x: x["dt"])
    total_events = len(all_events)
    print(f"Total eventos ordenados cronológicamente: {total_events:,}")
    print(f"Rango temporal: {all_events[0]['dt']} -> {all_events[-1]['dt']}")
    
    # Pre-index events by roulette for fast 30d window lookups
    events_by_r = {}
    for ev in all_events:
        events_by_r.setdefault(ev["ruleta"], []).append(ev)
        
    # We will test two ranking assignment paradigms:
    # Paradigm 1: Fixed Rank (Rank 1-3 Verde, 4-5 Amarillo, 6+ Rojo) - Exact code of bot_nuevas_ruletas.py
    # Paradigm 2: Proportional / Quantile (Top tier Verde, mid Amarillo, bottom Rojo adjusted to active count)
    
    for paradigm_name, is_quantile in [("PARADIGMA 1: RANKING FIJO BOT (Top 1-3 Verde, 4-5 Amarillo, 6+ Rojo)", False),
                                       ("PARADIGMA 2: TERCIL PROPORCIONAL DINÁMICO (37.5% Verde, 25% Amarillo, 37.5% Rojo)", True)]:
        print("\n" + "#" * 80)
        print(f"  {paradigm_name}")
        print("#" * 80)
        
        # We need to assign each event its color at the time of the event
        # Note: 30-day lookback STRICTLY before ev['dt'] (no lookahead bias)
        annotated_events = []
        
        # Track 30-day lookback dynamically
        # Since events are sorted by dt:
        for i, ev in enumerate(all_events):
            t = ev["dt"]
            t_30d = t - timedelta(days=30)
            
            # Find performance of all ruletas in [t_30d, t)
            # We consider ruletas that have at least 1 draw/event or are actively operating
            perf_30d = {}
            for r_name, r_evs in events_by_r.items():
                # Filter events strictly before t and >= t_30d
                recent = [e for e in r_evs if t_30d <= e["dt"] < t]
                if recent:
                    # Calculate net units PnL: sum(payout * hit - total_cands)
                    net_units = sum(e["payout"] if e["hit"] else 0 - e["total_cands"] for e in recent)
                    perf_30d[r_name] = net_units
                else:
                    # Check if this roulette had started before t
                    first_dt = r_evs[0]["dt"]
                    last_dt = r_evs[-1]["dt"]
                    if first_dt <= t <= last_dt:
                        perf_30d[r_name] = 0.0 # Active but no triggers in last 30d
                        
            # Sort ruletas by 30d PnL descending
            sorted_ruletas = sorted(perf_30d.items(), key=lambda x: x[1], reverse=True)
            n_active = len(sorted_ruletas)
            
            # Determine color of current roulette
            cur_r = ev["ruleta"]
            color = "VERDE" # default fallback
            stake = 1.50
            rank = 1
            
            for rk, (r_cand, pnl_val) in enumerate(sorted_ruletas, 1):
                if r_cand == cur_r:
                    rank = rk
                    break
                    
            if not is_quantile:
                # Fixed bot rule:
                if rank <= 3:
                    color = "VERDE"
                    stake = 1.50
                elif rank <= 5:
                    color = "AMARILLO"
                    stake = 1.00
                else:
                    color = "ROJO"
                    stake = 0.50
            else:
                # Proportional rule:
                if n_active <= 2:
                    color = "VERDE" if rank == 1 else "AMARILLO"
                    stake = 1.50 if rank == 1 else 1.00
                elif n_active <= 4:
                    if rank == 1:
                        color, stake = "VERDE", 1.50
                    elif rank == 2:
                        color, stake = "AMARILLO", 1.00
                    else:
                        color, stake = "ROJO", 0.50
                else:
                    # e.g. 5 to 8 ruletas
                    v_cut = max(1, round(n_active * 0.375))
                    a_cut = max(v_cut + 1, round(n_active * 0.625))
                    if rank <= v_cut:
                        color, stake = "VERDE", 1.50
                    elif rank <= a_cut:
                        color, stake = "AMARILLO", 1.00
                    else:
                        color, stake = "ROJO", 0.50
                        
            ev_copy = dict(ev)
            ev_copy["color"] = color
            ev_copy["stake_unit"] = stake
            ev_copy["rank_30d"] = rank
            ev_copy["n_active_30d"] = n_active
            annotated_events.append(ev_copy)
            
        # Now evaluate the THREE COMPARATIVE SCENARIOS:
        # Scenario 1: All Colors (Verde $1.50, Amarillo $1.00, Rojo $0.50)
        # Scenario 2: Two Colors (Verde $1.50, Amarillo $1.00) -> Exclude Rojo
        # Scenario 3: Only Verde (Verde $1.50) -> Exclude Amarillo & Rojo
        
        scenarios = [
            ("Escenario 1: Todos los Colores (Verde $1.50, Amarillo $1.00, Rojo $0.50)", ["VERDE", "AMARILLO", "ROJO"]),
            ("Escenario 2: Dos Colores (Verde $1.50 y Amarillo $1.00) [Excluye Rojo]", ["VERDE", "AMARILLO"]),
            ("Escenario 3: Solo Verde (Verde $1.50) [Excluye Amarillo y Rojo]", ["VERDE"])
        ]
        
        for sc_name, allowed_colors in scenarios:
            bets = 0
            wins = 0
            total_invested = 0.0
            total_returned = 0.0
            pnl_history = []
            running_pnl = 0.0
            peak_pnl = 0.0
            max_dd = 0.0
            
            # Monthly tracking
            monthly_pnl = {}
            
            for ev in annotated_events:
                if ev["color"] not in allowed_colors:
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
                    
                # Month tracking (YYYY-MM)
                m_key = str(ev["fecha"])[:7]
                monthly_pnl[m_key] = monthly_pnl.get(m_key, 0.0) + pnl
                
            net_pnl = total_returned - total_invested
            roi = (net_pnl / total_invested * 100.0) if total_invested > 0 else 0.0
            wr = (wins / bets * 100.0) if bets > 0 else 0.0
            profit_factor = (total_returned / total_invested) if total_invested > 0 else 0.0
            
            # Monthly metrics
            m_vals = list(monthly_pnl.values())
            pos_months = sum(1 for v in m_vals if v > 0)
            neg_months = sum(1 for v in m_vals if v < 0)
            total_months = len(m_vals)
            sharpe_monthly = (np.mean(m_vals) / np.std(m_vals) * np.sqrt(12)) if len(m_vals) > 1 and np.std(m_vals) > 0 else 0.0
            
            print("-" * 75)
            print(f"📊 {sc_name}")
            print("-" * 75)
            print(f"  • Disparos Realizados     : {bets:,} (Aciertos: {wins:,} | Win Rate: {wr:.2f}%)")
            print(f"  • Inversión Total         : ${total_invested:,.2f} USD")
            print(f"  • Total Cobrado           : ${total_returned:,.2f} USD")
            print(f"  • Ganancia Neta (PnL)     : {'+' if net_pnl>=0 else ''}${net_pnl:,.2f} USD")
            print(f"  • Retorno (ROI)           : {'+' if roi>=0 else ''}{roi:.2f}%")
            print(f"  • Factor de Beneficio     : {profit_factor:.3f}")
            print(f"  • Máximo Drawdown (Cash)  : -${max_dd:,.2f} USD")
            print(f"  • Meses Ganadores         : {pos_months} de {total_months} ({pos_months/total_months*100:.1f}%)")
            print(f"  • Sharpe Anualizado (Mes) : {sharpe_monthly:.2f}")

run_backtest_dynamic_colors()
