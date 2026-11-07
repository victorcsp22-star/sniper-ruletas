import os
import pandas as pd
import numpy as np
from sim_core import RULETAS, simulate_sniper_strategy
from audit_questions_1_2_3 import load_data

def evaluate_lag_permutations():
    print("=" * 115)
    print("PARTE 1: BÚSQUEDA EXHAUSTIVA DE COMBINACIONES DE LAGS ÓPTIMAS Y COMPRESIÓN DE CANDIDATOS")
    print("=" * 115)
    
    # Pruebas dirigidas por ruleta
    lag_experiments = {
        "Lotto Activo": [
            ("Actual [20, 18, 14]", [20, 18, 14]),
            ("Top-3 Z [20, 18, 19]", [20, 18, 19]),
            ("Top-2 Z [20, 18]", [20, 18]),
            ("Cuarteto [20, 18, 19, 14]", [20, 18, 19, 14]),
            ("Circadiano [20, 18, 55]", [20, 18, 55])
        ],
        "La Granjita": [
            ("Actual [15, 17]", [15, 17]),
            ("Top-3 Z [15, 14, 17]", [15, 14, 17]),
            ("Top-2 Z [15, 14]", [15, 14]),
            ("Alternativo [15, 14, 41]", [15, 14, 41]),
            ("Solo Top-1 [15]", [15])
        ],
        "Ruleta Royal": [
            ("Actual [16, 19, 31]", [16, 19, 31]),
            ("Top-2 Z [19, 16]", [19, 16]),
            ("Top-4 Z [19, 16, 31, 33]", [19, 16, 31, 33]),
            ("Alternativo [19, 16, 49]", [19, 16, 49])
        ],
        "Guacharo Activo": [
            ("Actual 5 Lags [31, 41, 25, 42, 35]", [31, 41, 25, 42, 35]),
            ("Top-3 Z [31, 41, 54]", [31, 41, 54]),
            ("Top-4 Z [31, 41, 54, 52]", [31, 41, 54, 52]),
            ("Top-2 Z [31, 41]", [31, 41]),
            ("Alternativo [31, 41, 25]", [31, 41, 25]),
            ("Cuarteto Podado [31, 41, 25, 54]", [31, 41, 25, 54])
        ],
        "Gatazo": [
            ("Actual [35, 22, 20]", [35, 22, 20]),
            ("Top-3 Z [35, 20, 9]", [35, 20, 9]),
            ("Top-2 Z [35, 20]", [35, 20]),
            ("Alternativo [35, 20, 53]", [35, 20, 53]),
            ("Cuarteto [35, 20, 9, 22]", [35, 20, 9, 22])
        ],
        "Mega Animal 40": [
            ("Actual [18, 21, 37]", [18, 21, 37]),
            ("Top-3 Z [18, 21, 20]", [18, 21, 20]),
            ("Top-2 Z [18, 21]", [18, 21]),
            ("Top-4 Z [18, 21, 20, 22]", [18, 21, 20, 22]),
            ("Alternativo [18, 21, 46]", [18, 21, 46])
        ],
        "Monje Millonario": [
            ("Actual [24, 35, 37]", [24, 35, 37]),
            ("Top-3 Z [24, 42, 48]", [24, 42, 48]),
            ("Top-2 Z [24, 42]", [24, 42]),
            ("Solo Top-1 [24]", [24]),
            ("Cuarteto [24, 42, 48, 52]", [24, 42, 48, 52])
        ],
        "Lotto Activo RD": [
            ("Actual [21, 39, 50]", [21, 39, 50]),
            ("Top-3 Z [50, 39, 51]", [50, 39, 51]),
            ("Top-2 Z [50, 39]", [50, 39]),
            ("Alternativo [50, 39, 48]", [50, 39, 48]),
            ("Cuarteto [50, 39, 51, 48]", [50, 39, 51, 48])
        ],
        "Lotto Gato": [
            ("Actual [19, 38, 16]", [19, 38, 16]),
            ("Top-3 Z [18, 26, 14]", [18, 26, 14]),
            ("Top-2 Z [18, 26]", [18, 26]),
            ("Cuarteto [18, 26, 14, 38]", [18, 26, 14, 38]),
            ("Alternativo [18, 38, 16]", [18, 38, 16])
        ],
        "Loto Chaima": [
            ("Actual [35, 29, 38]", [35, 29, 38]),
            ("Top-3 Z [49, 57, 35]", [49, 57, 35]),
            ("Top-2 Z [49, 57]", [49, 57]),
            ("Cuarteto [49, 57, 35, 51]", [49, 57, 35, 51])
        ]
    }
    
    for r_name, experiments in lag_experiments.items():
        cfg = RULETAS[r_name]
        if not os.path.exists(cfg["file"]):
            continue
        df = load_data(cfg["file"])
        payout = cfg["payout"]
        rec_w = cfg["rec_w"]
        target_streaks = cfg["target_streaks"]
        use_ac = (r_name in ["Lotto Activo", "Ruleta Royal"])
        
        print(f"\n===================================================================================================")
        print(f"RULETA: {r_name} (Payout: {payout}x, rec_w: {rec_w}, AC: {use_ac})")
        print(f"===================================================================================================")
        print(f"{'Configuración':<32} | {'Trades':<7} | {'WR %':<7} | {'Avg Cands':<10} | {'BE Rate %':<10} | {'ROI %':<8} | {'PnL ($)':<9} | {'FPR R1 %':<8}")
        print("-" * 105)
        
        base_res = None
        for label, lags in experiments:
            res = simulate_sniper_strategy(df, lags, rec_w, target_streaks, use_ac, payout)
            if base_res is None:
                base_res = res
            ccr = ((base_res['avg_cands'] - res['avg_cands']) / base_res['avg_cands'] * 100) if base_res['avg_cands'] > 0 else 0
            mark = " (BASE)" if label.startswith("Actual") else (f" [CCR: {ccr:+4.1f}%]" if ccr != 0 else "")
            print(f"{label:<32} | {res['trades']:<7} | {res['wr']:<7.2f} | {res['avg_cands']:<10.2f} | {res['be_rate']:<10.2f} | {res['roi']:<+8.2f} | {res['pnl']:<+9.1f} | {res['fpr_r1']:<8.2f}{mark}")

if __name__ == "__main__":
    evaluate_lag_permutations()
