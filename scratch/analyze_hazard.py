import os
import pandas as pd
import numpy as np

from audit_questions_1_2_3 import load_data, RULETAS

def analyze_repetition_hazard():
    print("=" * 115)
    print("FUNCIÓN DE RIESGO DE REPETICIÓN (HAZARD / REPETITION PROBABILITY POR DISTANCIA d = 1..15)")
    print("=" * 115)
    
    for r_name, cfg in RULETAS.items():
        if not os.path.exists(cfg["file"]):
            continue
        df = load_data(cfg["file"])
        nums = df['numero'].tolist()
        total = len(nums)
        k_uniq = len(set(nums))
        p0 = 1.0 / k_uniq
        
        print(f"\n>>> {r_name} (K={k_uniq}, p0={p0*100:.2f}%)")
        row_str = "  d:   " + " ".join([f"{d:>5d}" for d in range(1, 13)])
        print(row_str)
        
        prob_str = "  P%:  "
        edge_str = "  E%:  "
        
        for d in range(1, 13):
            matches = sum(1 for i in range(d, total) if nums[i] == nums[i - d])
            trials = total - d
            p_d = (matches / trials) * 100 if trials > 0 else 0
            edge_d = ((matches / trials) - p0) / p0 * 100 if trials > 0 else 0
            prob_str += f"{p_d:5.2f} "
            edge_str += f"{edge_d:+5.0f}%"
            
        print(prob_str)
        print(edge_str)

if __name__ == "__main__":
    analyze_repetition_hazard()
