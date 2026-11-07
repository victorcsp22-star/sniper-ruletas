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

def analyze_dd_and_streaks():
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
        
    for window_days in [15, 30]:
        print("=" * 80)
        print(f"ANÁLISIS DE DRAWDOWN (%) Y RACHAS - VENTANA MÓVIL DE {window_days} DÍAS")
        print("=" * 80)
        
        annotated = []
        for ev in all_events:
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
            sorted_r = sorted(perf.items(), key=lambda x: x[1], reverse=True)
            rank = 1
            for rk, (rc, _) in enumerate(sorted_r, 1):
                if rc == ev["ruleta"]:
                    rank = rk
                    break
            if rank <= 3: color, stake = "VERDE", 1.50
            elif rank <= 5: color, stake = "AMARILLO", 1.00
            else: color, stake = "ROJO", 0.50
            
            ec = dict(ev)
            ec["color"] = color
            ec["stake_unit"] = stake
            annotated.append(ec)
            
        scenarios = [
            ("Escenario 1 (Todos los Colores)", ["VERDE", "AMARILLO", "ROJO"]),
            ("Escenario 2 (Verde y Amarillo)", ["VERDE", "AMARILLO"]),
            ("Escenario 3 (Solo Verde)", ["VERDE"])
        ]
        
        for sc_name, allowed in scenarios:
            sub = [e for e in annotated if e["color"] in allowed]
            
            # 1. Streaks calculation
            cur_loss_streak = 0
            max_loss_streak = 0
            loss_streaks = []
            
            cur_win_streak = 0
            max_win_streak = 0
            win_streaks = []
            
            for e in sub:
                if e["hit"]:
                    if cur_loss_streak > 0:
                        loss_streaks.append(cur_loss_streak)
                        cur_loss_streak = 0
                    cur_win_streak += 1
                    if cur_win_streak > max_win_streak:
                        max_win_streak = cur_win_streak
                else:
                    if cur_win_streak > 0:
                        win_streaks.append(cur_win_streak)
                        cur_win_streak = 0
                    cur_loss_streak += 1
                    if cur_loss_streak > max_loss_streak:
                        max_loss_streak = cur_loss_streak
            if cur_loss_streak > 0: loss_streaks.append(cur_loss_streak)
            if cur_win_streak > 0: win_streaks.append(cur_win_streak)
            
            # 2. Equity and Drawdown calculations
            # Let's evaluate with an initial capital baseline of $1,000 USD and $500 USD
            # Also calculate percentage DD relative to Peak Accumulated Equity (Peak)
            
            # Starting bankroll = $1,000 USD (to absorb historical $559.50 cash DD without liquidation)
            b_init = 1000.0
            equity = [b_init]
            peak = b_init
            max_dd_pct_b1000 = 0.0
            max_dd_cash = 0.0
            dd_start_idx = None
            dd_duration_bets = 0
            max_dd_duration_bets = 0
            
            # Cumulative PnL curve
            cum_pnl = [0.0]
            peak_pnl = 0.0
            
            for idx, e in enumerate(sub):
                cost = e["stake_unit"] * e["total_cands"]
                won = e["stake_unit"] * e["payout"] if e["hit"] else 0.0
                pnl = won - cost
                
                new_b = equity[-1] + pnl
                equity.append(new_b)
                if new_b > peak:
                    peak = new_b
                dd_cash = peak - new_b
                dd_pct = (dd_cash / peak * 100.0) if peak > 0 else 0.0
                
                if dd_cash > max_dd_cash:
                    max_dd_cash = dd_cash
                if dd_pct > max_dd_pct_b1000:
                    max_dd_pct_b1000 = dd_pct
                    
                # Track duration of drawdown in consecutive bets
                if dd_cash > 0:
                    dd_duration_bets += 1
                    if dd_duration_bets > max_dd_duration_bets:
                        max_dd_duration_bets = dd_duration_bets
                else:
                    dd_duration_bets = 0
                    
            # Also evaluate if starting with $600 USD (bare minimum for $559.50 DD)
            b_init_600 = 600.0
            eq_600 = [b_init_600]
            pk_600 = b_init_600
            max_dd_pct_b600 = 0.0
            for e in sub:
                cost = e["stake_unit"] * e["total_cands"]
                won = e["stake_unit"] * e["payout"] if e["hit"] else 0.0
                pnl = won - cost
                new_b = eq_600[-1] + pnl
                eq_600.append(new_b)
                if new_b > pk_600: pk_600 = new_b
                dd_pct = (pk_600 - new_b) / pk_600 * 100.0
                if dd_pct > max_dd_pct_b600: max_dd_pct_b600 = dd_pct

            # Peak-Relative Drawdown (cuando el sistema ya tiene acumuladas ganancias):
            # When the drawdown occurred, what was the peak equity at that moment?
            # Let's find the exact date and peak when the -$559.50 happened:
            p_val = b_init
            p_top = b_init
            trough_date = None
            peak_before_trough = 0.0
            for idx, e in enumerate(sub):
                cost = e["stake_unit"] * e["total_cands"]
                won = e["stake_unit"] * e["payout"] if e["hit"] else 0.0
                pnl = won - cost
                p_val += pnl
                if p_val > p_top:
                    p_top = p_val
                if abs((p_top - p_val) - max_dd_cash) < 0.01:
                    trough_date = e["fecha"]
                    peak_before_trough = p_top
                    
            pct_at_moment = (max_dd_cash / peak_before_trough * 100.0) if peak_before_trough > 0 else 0.0
            
            print(f"\n>>> {sc_name} <<<")
            print(f"  • Disparos Totales:             {len(sub):,} (Aciertos: {sum(1 for e in sub if e['hit']):,})")
            print(f"  • Racha Máxima de Fallos (MDL): {max_loss_streak} disparos consecutivos sin acertar")
            print(f"  • Racha Promedio de Fallos:     {np.mean(loss_streaks):.2f} disparos")
            print(f"  • Racha Máxima de Aciertos:     {max_win_streak} aciertos consecutivos")
            print(f"  • Máximo Drawdown en Efectivo:  -${max_dd_cash:,.2f} USD")
            print(f"  • Fecha del Fondo del Drawdown: {trough_date}")
            print(f"  • DD % Real en el Momento Pico: {pct_at_moment:.2f}% (Pico previo: ${peak_before_trough:,.2f} USD)")
            print(f"  • DD % con Banca Base $1,000:   {max_dd_pct_b1000:.2f}%")
            print(f"  • DD % con Banca Base $600:     {max_dd_pct_b600:.2f}%")
            print(f"  • Duración Máx del DD:          {max_dd_duration_bets} disparos hasta recuperar nuevo ATH")

analyze_dd_and_streaks()
