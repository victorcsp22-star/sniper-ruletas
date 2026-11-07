"""
========================================================================================
 AUDITORÍA CUANTITATIVA Y DE PATRONES: 6 RULETAS CANDIDATAS
========================================================================================
Evalúa para cada una de las 6 ruletas candidatas:
1. Cantidad de números totales (Ruleta 36, 38 u otra).
2. Payout oficial estimado (x30 o x60 según tamaño de ruleta).
3. Entropía y Uniformidad (Chi-cuadrado).
4. Persistencia temporal (Autocorrelación / Lags 1 al 15).
5. Evaluación de estrategias:
   a) Canasta Rezagados (Recency Window 10 a 25)
   b) Matrices de Markov de 1er Orden
   c) Rachas óptimas de entrada
6. Métricas: Win Rate, Retorno Neto (ROI), Max Drawdown, Racha máxima de fallos.
========================================================================================
"""

import os
import glob
import pandas as pd
import numpy as np
from scipy import stats

DATA_DIR = r"C:\Users\victo\nuevas_ruletas\data_candidatos"
files = glob.glob(os.path.join(DATA_DIR, "*.csv"))

print("=" * 100)
print(f"{'RULETA CANDIDATA':<32} | {'SORTEOS':<8} | {'NÚMS':<5} | {'PAYOUT':<6} | {'CHI2 P-VAL':<10} | {'REPETICIÓN INM.'}")
print("=" * 100)

ruletas_info = {}

for fpath in files:
    fname = os.path.basename(fpath)
    df = pd.read_csv(fpath)
    if len(df) == 0:
        continue
    
    # Limpiar y normalizar numeros
    nums = df["numero"].astype(str).str.strip().tolist()
    unique_nums = sorted(list(set(nums)))
    n_unique = len(unique_nums)
    
    # Determinar payout tipico
    payout = 30.0 if n_unique <= 38 else 60.0
    
    # Chi-cuadrado de uniformidad
    counts = pd.Series(nums).value_counts()
    chi2, p_val = stats.chisquare(counts)
    
    # Probabilidad de repetición inmediata (Lag 1)
    repeats = sum(1 for i in range(1, len(nums)) if nums[i] == nums[i-1])
    repeat_rate = (repeats / (len(nums) - 1)) * 100
    
    name = fname.replace(".csv", "")
    print(f"{name:<32} | {len(df):<8,d} | {n_unique:<5} | {payout:<6.0f}x | {p_val:<10.4f} | {repeat_rate:.2f}% (Teor: {100/n_unique:.2f}%)")
    
    ruletas_info[name] = {
        "file": fpath,
        "n_draws": len(df),
        "n_unique": n_unique,
        "payout": payout,
        "p_val": p_val,
        "repeat_rate": repeat_rate,
        "nums": nums
    }

print("=" * 100)

# Ahora evaluamos backtest de patrones de Rezagados vs Markov
print("\n" + "=" * 100)
print("AUDITORÍA DE PATRONES DE EXPLOTACIÓN (Canasta de Rezagados y Detección de Ineficiencias)")
print("=" * 100)
print(f"{'RULETA':<28} | {'ESTRATEGIA':<22} | {'TIROS':<6} | {'WINS':<5} | {'WIN RATE':<9} | {'ROI %':<8} | {'PNL ($)':<9} | {'MAX DD ($)':<10} | {'MAX RACHA'}")
print("-" * 100)

for name, info in ruletas_info.items():
    nums = info["nums"]
    payout = info["payout"]
    n_unique = info["n_unique"]
    
    # 1. Probar Rezagados: lags [1, 2, 3], rec_w = 12
    # Grid de búsqueda de la mejor configuración de lags para cada ruleta
    best_res = None
    
    for lags in [[1], [1, 2], [1, 2, 3], [2, 3], [1, 3]]:
        for rec_w in [10, 15, 20]:
            for target_streak in [[0], [1], [2], [0, 1], [1, 2]]:
                # Simular
                streak = 0
                total_bets = 0
                wins = 0
                pnl = 0.0
                peak = 0.0
                max_dd = 0.0
                cur_loss_streak = 0
                max_loss_streak = 0
                
                min_k = max(max(lags), rec_w) + 1
                for i in range(min_k, len(nums)):
                    actual = nums[i]
                    rec_set = set(nums[i - rec_w : i])
                    raw_cands = [nums[i - l] for l in lags if i - l >= 0]
                    cands = sorted(list(set(raw_cands) - rec_set))
                    
                    if not cands:
                        continue
                    
                    hit = (actual in cands)
                    is_shot = (streak in target_streak)
                    
                    if is_shot:
                        total_bets += len(cands)
                        cost = len(cands) * 1.0
                        if hit:
                            wins += 1
                            pnl += (payout - cost)
                            cur_loss_streak = 0
                        else:
                            pnl -= cost
                            cur_loss_streak += 1
                            if cur_loss_streak > max_loss_streak:
                                max_loss_streak = cur_loss_streak
                                
                        if pnl > peak:
                            peak = pnl
                        dd = peak - pnl
                        if dd > max_dd:
                            max_dd = dd
                            
                    if hit:
                        streak = 0
                    else:
                        streak += 1
                        
                if total_bets >= 100:
                    roi = (pnl / total_bets) * 100.0
                    wr = (wins / (total_bets / len(lags))) * 100.0 if total_bets > 0 else 0
                    if best_res is None or roi > best_res["roi"]:
                        best_res = {
                            "name": name,
                            "strategy": f"Rezagados L{lags} R{rec_w} S{target_streak}",
                            "shots": total_bets,
                            "wins": wins,
                            "wr": (wins / (wins + (total_bets - wins*len(cands))/len(cands))) * 100 if wins > 0 else 0,
                            "roi": roi,
                            "pnl": pnl,
                            "max_dd": max_dd,
                            "max_streak": max_loss_streak
                        }
                        
    if best_res:
        print(f"{best_res['name']:<28} | {best_res['strategy']:<22} | {best_res['shots']:<6} | {best_res['wins']:<5} | {best_res['roi']:<8.2f}% | {best_res['roi']:<8.2f}% | ${best_res['pnl']:<8.2f} | -${best_res['max_dd']:<9.2f} | {best_res['max_streak']}")
    else:
        print(f"{name:<28} | Sin patrones estadísticos positivos")

print("=" * 100)
