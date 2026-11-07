import os
import sys
import pandas as pd
import numpy as np

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from sim_core import RULETAS
from audit_questions_1_2_3 import load_data

def test_purge_all_seen_today():
    print("=" * 115)
    print("TEST: PURGA TOTAL DE ANIMALES SALIDOS HOY (rec_set = rec_w UNION seen_today)")
    print("=" * 115)
    
    for r_name in ["Lotto Activo", "La Granjita", "Ruleta Royal", "Guacharo Activo", "Gatazo", "Mega Animal 40", "Monje Millonario"]:
        cfg = RULETAS[r_name]
        df = load_data(cfg["file"])
        nums = df['numero'].tolist()
        fechas = df['fecha'].tolist() if 'fecha' in df.columns else [''] * len(nums)
        payout = cfg['payout']
        rec_w = cfg['rec_w']
        lags = cfg['current_lags']
        target_streaks = cfg['target_streaks']
        use_ac = (r_name in ["Lotto Activo", "Ruleta Royal"])
        
        # 1. Base simulation
        min_idx = max(max(lags), 20)
        streak = 0
        trades_b, wins_b, cost_b = 0, 0, 0
        seen_today = set()
        last_fecha = None
        prev_was_repeat = False
        
        for i in range(min_idx, len(nums)):
            fecha = fechas[i]
            actual = nums[i]
            if fecha != last_fecha:
                seen_today = set()
                last_fecha = fecha
                prev_was_repeat = False
            rec_set = set(nums[i - rec_w:i])
            raw_cands = [nums[i - l] for l in lags if i >= l]
            cands = sorted(list(set(raw_cands) - rec_set))
            cost = len(cands)
            is_repeat_now = (actual in seen_today)
            skip = bool(use_ac and prev_was_repeat)
            hit = (actual in cands) if cost > 0 else False
            if cost > 0 and not skip:
                if streak in target_streaks:
                    trades_b += 1
                    cost_b += cost
                    if hit: wins_b += 1
                streak = 0 if hit else streak + 1
            elif cost > 0 and skip:
                streak = 0 if hit else streak + 1
            seen_today.add(actual)
            prev_was_repeat = is_repeat_now
            
        wr_b = (wins_b / trades_b * 100) if trades_b > 0 else 0
        avg_c_b = (cost_b / trades_b) if trades_b > 0 else 0
        roi_b = ((wins_b * payout - cost_b) / cost_b * 100) if cost_b > 0 else 0
        pnl_b = wins_b * payout - cost_b
        
        # 2. Strict Purge: rec_w UNION seen_today
        streak = 0
        trades_s, wins_s, cost_s = 0, 0, 0
        seen_today = set()
        last_fecha = None
        prev_was_repeat = False
        
        for i in range(min_idx, len(nums)):
            fecha = fechas[i]
            actual = nums[i]
            if fecha != last_fecha:
                seen_today = set()
                last_fecha = fecha
                prev_was_repeat = False
            rec_set = set(nums[i - rec_w:i]).union(seen_today) # STRICT PURGE
            raw_cands = [nums[i - l] for l in lags if i >= l]
            cands = sorted(list(set(raw_cands) - rec_set))
            cost = len(cands)
            is_repeat_now = (actual in seen_today)
            skip = bool(use_ac and prev_was_repeat)
            hit = (actual in cands) if cost > 0 else False
            if cost > 0 and not skip:
                if streak in target_streaks:
                    trades_s += 1
                    cost_s += cost
                    if hit: wins_s += 1
                streak = 0 if hit else streak + 1
            elif cost > 0 and skip:
                streak = 0 if hit else streak + 1
            seen_today.add(actual)
            prev_was_repeat = is_repeat_now
            
        wr_s = (wins_s / trades_s * 100) if trades_s > 0 else 0
        avg_c_s = (cost_s / trades_s) if trades_s > 0 else 0
        roi_s = ((wins_s * payout - cost_s) / cost_s * 100) if cost_s > 0 else 0
        pnl_s = wins_s * payout - cost_s
        ccr = ((avg_c_b - avg_c_s) / avg_c_b * 100)
        
        print(f"{r_name:<18} | BASE:   Trades={trades_b:4d} | WR={wr_b:5.2f}% | AvgC={avg_c_b:4.2f} | ROI={roi_b:+6.2f}% | PnL={pnl_b:+7.1f}")
        print(f"{r_name:<18} | PURGA:  Trades={trades_s:4d} | WR={wr_s:5.2f}% | AvgC={avg_c_s:4.2f} | ROI={roi_s:+6.2f}% | PnL={pnl_s:+7.1f} | CCR={ccr:+5.1f}%")
        print("-" * 105)

if __name__ == "__main__":
    test_purge_all_seen_today()
