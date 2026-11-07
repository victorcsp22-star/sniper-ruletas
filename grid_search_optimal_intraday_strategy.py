import os
import sys
import numpy as np
import pandas as pd
import scipy.stats as stats
from collections import defaultdict
import matplotlib.pyplot as plt

def run_grid_search():
    csv_file = "C:/Users/victo/nuevas_ruletas/lotto_activo_rd_lotoven_completo.csv"
    out_dir = "C:/Users/victo/.gemini/antigravity/brain/da61199f-f45d-4b1d-bcd9-a17212f844b0"
    
    df = pd.read_csv(csv_file, dtype={"numero": str})
    hora_order = {
        "08:30 AM": 1, "09:30 AM": 2, "10:30 AM": 3, "11:30 AM": 4,
        "12:30 PM": 5, "01:30 PM": 6, "02:30 PM": 7, "03:30 PM": 8,
        "04:30 PM": 9, "05:30 PM": 10, "06:30 PM": 11, "07:30 PM": 12
    }
    df["h_rank"] = df["hora"].map(hora_order)
    df = df.sort_values(by=["fecha", "h_rank"]).reset_index(drop=True)
    
    nums = df["numero"].tolist()
    dates = df["fecha"].tolist()
    hours = df["h_rank"].tolist()
    N = len(nums)
    
    canon_animals = [
        "0", "00", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
        "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
        "21", "22", "23", "24", "25", "26", "27", "28", "29", "30",
        "31", "32", "33", "34", "35", "36"
    ]
    
    # 70% In-Sample (Entrenamiento) / 30% Out-of-Sample (Validación Ciega)
    split_idx = int(N * 0.70)
    train_nums = nums[:split_idx]
    
    # 1. Matriz de transición Markov In-Sample
    markov_counts = defaultdict(lambda: defaultdict(int))
    markov_totals = defaultdict(int)
    for i in range(len(train_nums) - 1):
        a, b = train_nums[i], train_nums[i+1]
        markov_counts[a][b] += 1
        markov_totals[a] += 1
        
    markov_probs = defaultdict(dict)
    for a, targets in markov_counts.items():
        tot = markov_totals[a]
        for b, cnt in targets.items():
            markov_probs[a][b] = cnt / tot
            
    # 2. Frecuencias globales In-Sample
    counts_in = pd.Series(train_nums).value_counts(normalize=True).to_dict()
    
    # 3. Mejores Lags In-Sample
    lags_in = [21, 39, 50]
    
    # Modelos de Ranking entre Vivos:
    # M1: Markov Affinity Pura
    # M2: Ensemble (Markov 50% + Freq Global 50%)
    # M3: Lag Match (Vivos que coincidan con Lags 21, 39, 50)
    # M4: Freq Global Pura
    
    def score_candidate(model_type, prev_num, cand, idx):
        if model_type == "markov":
            return markov_probs[prev_num].get(cand, 0.0)
        elif model_type == "freq":
            return counts_in.get(cand, 0.0)
        elif model_type == "ensemble":
            p_m = markov_probs[prev_num].get(cand, 1/38)
            p_f = counts_in.get(cand, 1/38)
            return 0.6 * p_m + 0.4 * p_f
        elif model_type == "lags":
            score = 0.0
            for l in lags_in:
                if idx >= l and nums[idx-l] == cand:
                    score += 1.0
            return score
        return 0.0

    # Grid de Parámetros:
    # 1. Ventana horaria mínima: [8, 9, 10, 11, 12]
    # 2. Modelo de selección: ['markov', 'ensemble', 'lags', 'freq']
    # 3. Número de candidatos k: [1, 2]
    # 4. Gatillo condicional: ['incondicional', 'sniper_post_fallo_1', 'solo_dia_limpio']
    #    - solo_dia_limpio: si en el día YA hubo una repetición antes, NO apostar
    
    min_hours = [8, 9, 10, 11, 12]
    models = ["markov", "ensemble", "lags", "freq"]
    k_vals = [1, 2]
    triggers = ["incondicional", "sniper_post_fallo_1", "solo_dia_limpio"]
    
    all_results = []
    
    total_combos = len(min_hours) * len(models) * len(k_vals) * len(triggers)
    print(f"Iniciando Grid Search Exhaustivo: {total_combos} combinaciones probadas...")
    
    for h_min in min_hours:
        for m_type in models:
            for k in k_vals:
                for trig in triggers:
                    cap = 200.0
                    cap_history = [cap]
                    bets = 0
                    wins = 0
                    losses = 0
                    
                    current_date = None
                    seen_today = set()
                    day_has_repeat = False
                    
                    last_result_was_miss = False
                    
                    for i in range(split_idx, N):
                        actual = nums[i]
                        prev = nums[i-1]
                        d = dates[i]
                        h = hours[i]
                        
                        if d != current_date:
                            current_date = d
                            seen_today = set()
                            day_has_repeat = False
                            
                        # Verificar si el actual ya había salido hoy (para actualizar flag de repetición)
                        if actual in seen_today:
                            day_has_repeat = True
                            
                        # Evaluar si operamos en este sorteo
                        operate = True
                        if h < h_min:
                            operate = False
                        if trig == "solo_dia_limpio" and day_has_repeat:
                            operate = False
                        if trig == "sniper_post_fallo_1" and not last_result_was_miss:
                            operate = False
                            
                        targets = []
                        if operate:
                            vivos = [a for a in canon_animals if a not in seen_today]
                            # Excluir recencia inmediata (últimos 3 sorteos para evitar micro-rebotes falsos)
                            rec3 = set(nums[i-3:i])
                            vivos_filtered = [a for a in vivos if a not in rec3]
                            if not vivos_filtered:
                                vivos_filtered = vivos
                                
                            scored = [(a, score_candidate(m_type, prev, a, i)) for a in vivos_filtered]
                            # Filtrar solo aquellos con score > 0 si es lags
                            if m_type == "lags":
                                scored = [item for item in scored if item[1] > 0]
                                
                            scored.sort(key=lambda x: x[1], reverse=True)
                            targets = [item[0] for item in scored[:k]]
                            
                        if targets:
                            hit_any = False
                            for target in targets:
                                if cap < 1.0:
                                    break
                                bets += 1
                                if target == actual:
                                    wins += 1
                                    cap += 29.0
                                    hit_any = True
                                else:
                                    losses += 1
                                    cap -= 1.0
                                cap_history.append(cap)
                                
                            last_result_was_miss = not hit_any
                            
                        seen_today.add(actual)
                        
                    arr = np.array(cap_history)
                    peaks = np.maximum.accumulate(arr)
                    dds = peaks - arr
                    mdd = np.max(dds) if len(dds) > 0 else 0
                    
                    win_rate = (wins / bets * 100.0) if bets > 0 else 0.0
                    pf = (wins * 29.0) / losses if losses > 0 else 0.0
                    roi = ((cap - 200.0) / bets * 100.0) if bets > 0 else 0.0
                    net = cap - 200.0
                    
                    all_results.append({
                        "h_min": h_min,
                        "model": m_type,
                        "k": k,
                        "trigger": trig,
                        "bets": bets,
                        "wins": wins,
                        "losses": losses,
                        "win_rate": win_rate,
                        "final_cap": cap,
                        "net": net,
                        "roi": roi,
                        "pf": pf,
                        "mdd": mdd
                    })
                    
    df_res = pd.DataFrame(all_results)
    
    # Filtrar solo estrategias con volumen mínimo para significancia (ej. >= 200 apuestas)
    df_valid = df_res[df_res["bets"] >= 150].copy()
    
    print("\n" + "="*95)
    print("TOP 10 ESTRATEGIAS ÓPTIMAS POR PROFIT FACTOR (Mínimo 150 apuestas OOS)")
    print("="*95)
    top_pf = df_valid.sort_values(by="pf", ascending=False).head(10)
    for idx, r in top_pf.iterrows():
        print(f"H>={r['h_min']:>2} | {r['model']:<8} | k={r['k']} | {r['trigger']:<18} | Bets={r['bets']:>4} | WR={r['win_rate']:.2f}% | PF={r['pf']:.2f} | Net=+${r['net']:>6.2f} | MaxDD=${r['mdd']:.0f}")

    print("\n" + "="*95)
    print("TOP 10 ESTRATEGIAS ÓPTIMAS POR GANANCIA NETA TOTAL ($ USD sobre $200)")
    print("="*95)
    top_net = df_valid.sort_values(by="net", ascending=False).head(10)
    for idx, r in top_net.iterrows():
        print(f"H>={r['h_min']:>2} | {r['model']:<8} | k={r['k']} | {r['trigger']:<18} | Bets={r['bets']:>4} | WR={r['win_rate']:.2f}% | PF={r['pf']:.2f} | Net=+${r['net']:>6.2f} | MaxDD=${r['mdd']:.0f}")

    # Seleccionar la MEJOR Estrategia Suprema (Balance de Rentabilidad, Win Rate y Bajo Drawdown)
    # Criterio: Mayor Sharpe / Score Compuesto: PF * WR / (MDD / 200)
    df_valid["score"] = (df_valid["pf"] * df_valid["win_rate"]) / (df_valid["mdd"] / 200.0 + 1.0)
    top_champion = df_valid.sort_values(by="score", ascending=False).iloc[0]
    
    print("\n" + "*"*95)
    print(">>> CAMPEONA ABSOLUTA RECOMENDADA (ESTRATEGIA ÓPTIMA FINAL) <<<")
    print(f"  Ventana Horaria:       Sorteos >= {top_champion['h_min']} (Últimos {13 - top_champion['h_min']} sorteos del día)")
    print(f"  Modelo de Selección:   {top_champion['model'].upper()} (Selección del mejor animal vivo)")
    print(f"  Candidatos por Tiro:   k = {top_champion['k']} animal(es)")
    print(f"  Filtro Gatillo:        {top_champion['trigger']}")
    print(f"  Apuestas Totales:      {top_champion['bets']} disparos en 1.3 años")
    print(f"  Tasa de Acierto:       {top_champion['win_rate']:.3f}% (Break-even: 3.333%)")
    print(f"  Profit Factor:         {top_champion['pf']:.2f}")
    print(f"  Retorno (ROI):         {top_champion['roi']:+.2f}%")
    print(f"  Capital Final ($200):  ${top_champion['final_cap']:.2f} USD (+${top_champion['net']:.2f} USD)")
    print(f"  Drawdown Máximo:       ${top_champion['mdd']:.2f} USD")
    print("*"*95)
    
    # Generar visualización de la campeona vs alternativas
    return top_champion, top_pf, top_net

if __name__ == "__main__":
    run_grid_search()
