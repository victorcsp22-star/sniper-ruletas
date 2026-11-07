"""
========================================================================================
 BACKTEST DE EXPLOTACIÓN: ANOMALÍA DEL #0 Y CADENAS DE MARKOV EN CHANCE A Y B
========================================================================================
Estrategias a evaluar:
1. Apuesta pura al #0 cuando sale un disparador de alta transición (Markov > 7%).
2. Apuesta a los top 3 candidatos condicionales de Markov.
========================================================================================
"""

import pandas as pd
import numpy as np

for name in ["chance_con_animalitos_a", "chance_con_animalitos_b"]:
    df = pd.read_csv(f"C:/Users/victo/nuevas_ruletas/data_candidatos/{name}.csv")
    nums = df["numero"].astype(int).tolist()
    n = len(nums)
    
    # 1. Matriz de transicion con ventana rodante para evitar lookahead bias
    # Usamos los primeros 2,000 tiros para calibrar y el resto para operar
    calib = 2000
    train_nums = nums[:calib]
    test_nums = nums[calib:]
    
    # Construir probabilidades con train
    from collections import defaultdict, Counter
    counts = defaultdict(Counter)
    for i in range(1, len(train_nums)):
        counts[train_nums[i-1]][train_nums[i]] += 1
        
    # Identificar pares con prob > 7.0%
    hot_pairs = {}
    for prev, counter in counts.items():
        tot = sum(counter.values())
        for nxt, cnt in counter.items():
            prob = cnt / tot
            if prob >= 0.07: # 7% vs 3.33% de payout
                if prev not in hot_pairs:
                    hot_pairs[prev] = []
                hot_pairs[prev].append(nxt)
                
    print(f"\n--- BACKTEST SIN LOOKAHEAD BIAS EN {name.upper()} ---")
    print(f"Pares calificados (Prob >= 7.0% en calibración): {sum(len(v) for v in hot_pairs.values())}")
    
    # Evaluar en test_nums
    payout = 30.0
    pnl = 0.0
    bets = 0
    wins = 0
    peak = 0.0
    max_dd = 0.0
    
    for i in range(1, len(test_nums)):
        prev = test_nums[i-1]
        actual = test_nums[i]
        
        if prev in hot_pairs:
            cands = hot_pairs[prev]
            cost = len(cands) * 1.0
            bets += len(cands)
            hit = (actual in cands)
            if hit:
                wins += 1
                pnl += (payout - cost)
            else:
                pnl -= cost
                
            if pnl > peak:
                peak = pnl
            dd = peak - pnl
            if dd > max_dd:
                max_dd = dd
                
    roi = (pnl / bets) * 100.0 if bets > 0 else 0
    print(f"Tiros: {bets} | Aciertos: {wins} | Win Rate: {(wins/bets)*100 if bets>0 else 0:.2f}% (Teor: 3.33%)")
    print(f"PnL Neto: ${pnl:.2f} USD | ROI: {roi:.2f}% | Max Drawdown: -${max_dd:.2f} USD")
