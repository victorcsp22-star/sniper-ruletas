import os
import sys
import pandas as pd
import numpy as np

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from sim_core import RULETAS, simulate_sniper_strategy
from audit_questions_1_2_3 import load_data

def test_voting_and_intraday_filters():
    print("=" * 115)
    print("TEST: RESTRICCIÓN DE VOTANTES (OVERLAP DE LAGS) Y PURGA DE FRECUENCIA INTRADÍA")
    print("=" * 115)
    
    # 1. Probar en las ruletas principales si el solapamiento de lags aumenta el Win Rate
    for r_name in ["Lotto Activo", "Mega Animal 40", "Gatazo", "Guacharo Activo"]:
        cfg = RULETAS[r_name]
        df = load_data(cfg["file"])
        nums = df['numero'].tolist()
        payout = cfg['payout']
        rec_w = cfg['rec_w']
        lags = cfg['current_lags']
        
        # Evaluar distribución de candidatos únicos vs múltiples votos
        total_eval = 0
        hits_single = 0
        trials_single = 0
        hits_multi = 0
        trials_multi = 0
        
        for i in range(max(lags) + rec_w, len(nums)):
            rec_set = set(nums[i - rec_w:i])
            actual = nums[i]
            lag_cands = [nums[i - l] for l in lags]
            # Filtrar purgados
            valid_cands = [c for c in lag_cands if c not in rec_set]
            
            # Contar votos
            counts = pd.Series(valid_cands).value_counts()
            for cand, cnt in counts.items():
                if cnt == 1:
                    trials_single += 1
                    if cand == actual:
                        hits_single += 1
                elif cnt >= 2:
                    trials_multi += 1
                    if cand == actual:
                        hits_multi += 1
                        
        p_single = (hits_single / trials_single * 100) if trials_single > 0 else 0
        p_multi = (hits_multi / trials_multi * 100) if trials_multi > 0 else 0
        
        print(f"\n>>> {r_name} (Payout: {payout}x):")
        print(f"    Candidato con 1 solo lag de apoyo:  {hits_single:4d} / {trials_single:5d} -> WR = {p_single:5.2f}%")
        print(f"    Candidato con >=2 lags de apoyo:   {hits_multi:4d} / {trials_multi:5d} -> WR = {p_multi:5.2f}%")
        diff_lift = ((p_multi - p_single) / p_single * 100) if p_single > 0 else 0
        print(f"    🚀 LIFT por Coincidencia Armónica:  {diff_lift:+5.1f}% de sobre-rendimiento!")

def test_adaptive_intraday_recency():
    print("\n" + "=" * 115)
    print("TEST: PURGA ADAPTATIVA DE FRECUENCIA INVERSA (rec_w BASE + PURGA DE MULTI-APARICIÓN INTRADÍA)")
    print("=" * 115)
    
    for r_name in ["Lotto Activo", "La Granjita", "Ruleta Royal", "Guacharo Activo", "Mega Animal 40", "Gatazo"]:
        cfg = RULETAS[r_name]
        df = load_data(cfg["file"])
        payout = cfg["payout"]
        rec_w = cfg["rec_w"]
        lags = cfg["current_lags"]
        target_streaks = cfg["target_streaks"]
        use_ac = (r_name in ["Lotto Activo", "Ruleta Royal"])
        
        # 1. Base rec_w
        res_base = simulate_sniper_strategy(df, lags, rec_w, target_streaks, use_ac, payout)
        
        # 2. Adaptativa: si un número ya salió 2 o más veces hoy, se purga independientemente de rec_w
        nums = df['numero'].tolist()
        fechas = df['fecha'].tolist() if 'fecha' in df.columns else [''] * len(nums)
        min_idx = max(max(lags), 20)
        streak = 0
        trades_executed = 0
        trades_won = 0
        total_cost = 0
        seen_today_counts = {}
        last_fecha = None
        prev_was_repeat = False
        
        for i in range(min_idx, len(nums)):
            fecha = fechas[i]
            actual = nums[i]
            if fecha != last_fecha:
                seen_today_counts = {}
                last_fecha = fecha
                prev_was_repeat = False
                
            rec_set = set(nums[i - rec_w:i])
            # Purga adicional: si ya salió >= 2 veces hoy
            freq_purge = {n for n, c in seen_today_counts.items() if c >= 2}
            full_rec_set = rec_set.union(freq_purge)
            
            raw_cands = [nums[i - l] for l in lags if i >= l]
            cands = sorted(list(set(raw_cands) - full_rec_set))
            cost = len(cands)
            
            is_repeat_now = (actual in seen_today_counts)
            skip_shot = bool(use_ac and prev_was_repeat)
            hit = (actual in cands) if cost > 0 else False
            
            if cost > 0 and not skip_shot:
                if streak in target_streaks:
                    trades_executed += 1
                    total_cost += cost
                    if hit:
                        trades_won += 1
                streak = 0 if hit else streak + 1
            elif cost > 0 and skip_shot:
                streak = 0 if hit else streak + 1
                
            seen_today_counts[actual] = seen_today_counts.get(actual, 0) + 1
            prev_was_repeat = is_repeat_now
            
        wr = (trades_won / trades_executed * 100) if trades_executed > 0 else 0
        avg_c = (total_cost / trades_executed) if trades_executed > 0 else 0
        pnl = (trades_won * payout) - total_cost
        roi = (pnl / total_cost * 100) if total_cost > 0 else 0
        ccr = ((res_base['avg_cands'] - avg_c) / res_base['avg_cands'] * 100)
        
        print(f"{r_name:<18} | BASE:      Trades={res_base['trades']:4d} | WR={res_base['wr']:5.2f}% | AvgCands={res_base['avg_cands']:4.2f} | ROI={res_base['roi']:+6.2f}% | PnL={res_base['pnl']:+7.1f}")
        print(f"{r_name:<18} | ADAPTATIVA:Trades={trades_executed:4d} | WR={wr:5.2f}% | AvgCands={avg_c:4.2f} | ROI={roi:+6.2f}% | PnL={pnl:+7.1f} | CCR={ccr:+4.1f}%")
        print("-" * 105)

if __name__ == "__main__":
    test_voting_and_intraday_filters()
    test_adaptive_intraday_recency()
