import os
import pandas as pd
import numpy as np
from sim_core import RULETAS, simulate_sniper_strategy

def load_data(path):
    df = pd.read_csv(path, dtype={'numero': str})
    df['numero'] = df['numero'].astype(str).str.strip()
    if 'fecha' in df.columns and 'hora' in df.columns:
        df['dt'] = pd.to_datetime(df['fecha'] + ' ' + df['hora'], format='%Y-%m-%d %I:%M %p', errors='coerce')
        df = df.dropna(subset=['dt']).sort_values('dt').reset_index(drop=True)
    return df

def run_rec_w_sweep():
    print("=" * 115)
    print("PARTE 2: BARRIDO SISTEMÁTICO DE VENTANA DE PURGA DE RECENCIA (rec_w = 4, 6, 8, 10, 12)")
    print("=" * 115)
    
    for r_name, cfg in RULETAS.items():
        if not os.path.exists(cfg["file"]):
            continue
        df = load_data(cfg["file"])
        payout = cfg["payout"]
        lags = cfg["current_lags"]
        target_streaks = cfg["target_streaks"]
        use_ac = (r_name in ["Lotto Activo", "Ruleta Royal"])
        
        print(f"\n--- {r_name} (Payout: {payout}x, Lags: {lags}, AC: {use_ac}) ---")
        print(f"{'rec_w':<6} | {'Trades':<7} | {'Wins':<5} | {'WR %':<7} | {'Avg Cands':<10} | {'BE Rate %':<10} | {'ROI %':<8} | {'PnL ($)':<9} | {'FPR R1 %':<8}")
        print("-" * 88)
        
        for rw in [2, 4, 5, 6, 7, 8, 9, 10, 12]:
            res = simulate_sniper_strategy(df, lags, rw, target_streaks, use_ac, payout)
            marker = " <-- ACTUAL" if rw == cfg["rec_w"] else ""
            print(f"{rw:<6} | {res['trades']:<7} | {res['wins']:<5} | {res['wr']:<7.2f} | {res['avg_cands']:<10.2f} | {res['be_rate']:<10.2f} | {res['roi']:<+8.2f} | {res['pnl']:<+9.1f} | {res['fpr_r1']:<8.2f}{marker}")

def run_anti_clustering_audit():
    print("\n" + "=" * 115)
    print("PARTE 3: EVALUACIÓN DE LA COMPUERTA ANTI-CLUSTERING EN TODAS LAS RULETAS (False vs True)")
    print("=" * 115)
    print(f"{'Ruleta':<22} | {'AC Mode':<8} | {'Trades':<7} | {'WR %':<7} | {'Avg Cands':<10} | {'ROI %':<9} | {'PnL ($)':<9} | {'Diff ROI':<9}")
    print("-" * 95)
    
    for r_name, cfg in RULETAS.items():
        if not os.path.exists(cfg["file"]):
            continue
        df = load_data(cfg["file"])
        payout = cfg["payout"]
        lags = cfg["current_lags"]
        rec_w = cfg["rec_w"]
        target_streaks = cfg["target_streaks"]
        
        res_off = simulate_sniper_strategy(df, lags, rec_w, target_streaks, False, payout)
        res_on = simulate_sniper_strategy(df, lags, rec_w, target_streaks, True, payout)
        
        diff_roi = res_on['roi'] - res_off['roi']
        diff_pnl = res_on['pnl'] - res_off['pnl']
        
        act_str = "(ON en Prod)" if r_name in ["Lotto Activo", "Ruleta Royal"] else "(OFF en Prod)"
        
        print(f"{r_name:<22} | OFF      | {res_off['trades']:<7} | {res_off['wr']:<7.2f} | {res_off['avg_cands']:<10.2f} | {res_off['roi']:<+9.2f} | {res_off['pnl']:<+9.1f} | BASE")
        print(f"{r_name + ' ' + act_str:<22} | ON       | {res_on['trades']:<7} | {res_on['wr']:<7.2f} | {res_on['avg_cands']:<10.2f} | {res_on['roi']:<+9.2f} | {res_on['pnl']:<+9.1f} | {diff_roi:+7.2f}%")
        print("-" * 95)

if __name__ == "__main__":
    run_rec_w_sweep()
    run_anti_clustering_audit()
