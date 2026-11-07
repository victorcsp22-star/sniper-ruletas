import os, sys
import pandas as pd
import numpy as np
from experimento_ampliacion import preloaded_data

def simulate_per_ruleta_expansion():
    results = []
    for r_name, d in preloaded_data.items():
        nums = d["nums"]
        dates = d["dates"]
        base_lags = list(d["lags"])
        target_stk = d["target_stk"]
        rec_w = d["rec_w"]
        use_anti = d["use_anti"]
        blacklist = d["blacklist"]
        payout = d["payout"]
        
        # Test 1: 3 Lags (Baseline)
        # Test 2: 4 Lags (+1)
        for modo, lags in [("3 Lags (Base)", base_lags), ("4 Lags (+1)", base_lags + [base_lags[0] + 7])]:
            min_k = max(max(lags), rec_w) + 1
            streak = 0
            cur_d = None
            seen_today = set()
            prev_was_repeat = False
            
            ops, hits, cost, win = 0, 0, 0, 0
            dd_list = []
            cum = 0
            peak = 0
            
            for i in range(min_k, len(nums)):
                act = nums[i]
                dt = dates[i]
                if dt != cur_d:
                    cur_d = dt
                    seen_today = set()
                    prev_was_repeat = False
                    
                rec_set = set(nums[i - rec_w : i])
                raw_cands = [nums[i - l] for l in lags if i - l >= 0]
                cands_lag = sorted(list((set(raw_cands) - rec_set) - blacklist))
                
                skip_anti = bool(use_anti and prev_was_repeat)
                trigger = (streak in target_stk) and (not skip_anti) and (len(cands_lag) > 0)
                
                if trigger:
                    hit = (act in cands_lag)
                    c = len(cands_lag) * 1.0
                    w = payout if hit else 0.0
                    ops += 1
                    if hit: hits += 1
                    cost += c
                    win += w
                    cum += (w - c)
                    if cum > peak: peak = cum
                    dd_list.append(cum - peak)
                    
                if cands_lag and not skip_anti:
                    hit_c = (act in cands_lag)
                    streak = 0 if hit_c else streak + 1
                elif cands_lag and skip_anti:
                    hit_c = (act in cands_lag)
                    streak = 0 if hit_c else streak + 1
                    
                is_rep = (act in seen_today)
                seen_today.add(act)
                prev_was_repeat = is_rep
                
            pnl = win - cost
            roi = (pnl / cost * 100) if cost > 0 else 0
            wr = (hits / ops * 100) if ops > 0 else 0
            m_dd = min(dd_list) if dd_list else 0
            results.append({
                "ruleta": r_name,
                "modo": modo,
                "ops": ops,
                "hits": hits,
                "wr": wr,
                "inv": cost,
                "pnl": pnl,
                "roi": roi,
                "dd": m_dd
            })
            
    df_res = pd.DataFrame(results)
    return df_res

df_comp = simulate_per_ruleta_expansion()

print("="*95)
print("COMPARATIVA POR RULETA: BASELINE (3 LAGS) VS EXPANSION A 4 LAGS")
print("="*95)
for r_name, grp in df_comp.groupby('ruleta'):
    print(f"\n[*] {r_name}:")
    for idx, r in grp.iterrows():
        print(f"   - {r['modo']:<15} | Ops: {r['ops']:4d} | WR: {r['wr']:5.2f}% | Inv: ${r['inv']:<7,.0f} | PnL: {r['pnl']:+8,.1f} $ | ROI: {r['roi']:+6.1f}% | DD: ${r['dd']:<5,.0f}")
