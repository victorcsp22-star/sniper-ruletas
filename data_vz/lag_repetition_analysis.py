import numpy as np
import pandas as pd
from scipy import stats

def analyze_lags():
    csv_path = r"C:\Users\victo\.gemini\antigravity\scratch\lotto_activo_bot\lotto_activo_2anios.csv"
    df = pd.read_csv(csv_path, encoding='utf-8-sig', dtype={'numero': str})
    
    # Chronological sort
    df['sort_key'] = pd.to_datetime(df['fecha'] + ' ' + df['hora'], format='%Y-%m-%d %I:%M %p', errors='coerce')
    df = df.sort_values(by='sort_key').reset_index(drop=True)
    
    total = len(df)
    k_universe = 38
    p0 = 1.0 / k_universe # 0.026315789 (2.6316%)
    
    print("=========================================================================================")
    print("   ANÁLISIS DE REPETICIÓN POR DISTANCIA (LAGS 1 A 38): CONVERGENCIA A LA PROBABILIDAD REAL")
    print("=========================================================================================")
    print(f"Total de sorteos: {total:,}")
    print(f"Probabilidad teórica uniforme H0: p0 = 1/38 = {p0*100:.4f}%\n")
    
    max_lag = 38
    results = []
    
    for lag in range(1, max_lag + 1):
        # Sorteo actual vs sorteo de hace 'lag' turnos
        matches = (df['numero'] == df['numero'].shift(lag)).sum()
        valid_trials = total - lag
        p_hat = matches / valid_trials
        
        # Error estándar bajo H0
        se = np.sqrt(p0 * (1.0 - p0) / valid_trials)
        z_score = (p_hat - p0) / se
        p_value = 2.0 * (1.0 - stats.norm.cdf(abs(z_score)))
        
        # Intervalo de confianza 95% empírico
        se_hat = np.sqrt(p_hat * (1.0 - p_hat) / valid_trials)
        ci_lower = max(0, p_hat - 1.96 * se_hat)
        ci_upper = p_hat + 1.96 * se_hat
        
        results.append({
            'lag': lag,
            'matches': matches,
            'trials': valid_trials,
            'p_hat': p_hat,
            'pct': p_hat * 100,
            'z_score': z_score,
            'p_value': p_value,
            'ci_lower': ci_lower * 100,
            'ci_upper': ci_upper * 100,
            'significant': p_value < 0.05
        })
        
    df_res = pd.DataFrame(results)
    
    print(f"{'Lag (Distancia)':<15} | {'Repeticiones':<12} | {'Probabilidad':<14} | {'Esperado Teórico':<16} | {'Z-Score':<9} | {'Valor p':<9} | {'¿Significativo?'}")
    print("-" * 100)
    for _, r in df_res.iterrows():
        sig_str = "SÍ (ANOMALÍA)" if r['significant'] else "No (Normal)"
        direction = "[-]" if r['z_score'] < -2 else ("[+]" if r['z_score'] > 2 else "   ")
        print(f"Lag {int(r['lag']):<2} ({int(r['lag'])} sorteo atrás) | {int(r['matches']):<5} / {int(r['trials']):<5} | {r['pct']:>6.2f}% ({r['ci_lower']:4.2f}%-{r['ci_upper']:4.2f}%) | 2.63% (~{valid_trials*p0:.0f}) | {direction} {r['z_score']:>+6.2f} | {r['p_value']:>7.4f} | {sig_str}")

    print("\n-----------------------------------------------------------------------------------------")
    print("ANÁLISIS DE REPETICIÓN ACUMULADA: ¿QUÉ PROBABILIDAD HAY DE QUE EL NUEVO SORTEO")
    print("SEA CUALQUIERA DE LOS ÚLTIMOS M ANIMALES YA SALIDOS?")
    print("-----------------------------------------------------------------------------------------")
    
    # Evaluar ventana móvil de los últimos M animales
    # Teóricamente, si fueran M animales distintos elegidos al azar, P(X_t in {X_{t-1}..X_{t-M}})
    # Empíricamente, ¿cuál es la probabilidad real?
    for m in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]:
        hits = 0
        total_eval = 0
        for i in range(m, total):
            recent_set = set(df['numero'].iloc[i-m:i])
            current = df['numero'].iloc[i]
            if current in recent_set:
                hits += 1
            total_eval += 1
        pct = (hits / total_eval) * 100
        # Teórico promedio si cada sorteo es independiente
        # P(at least one match) = 1 - (1 - 1/38)^len(unique recent)
        print(f"Ventana de últimos {m:2d} sorteos: Salió uno de ellos {hits:4d} veces ({pct:5.2f}%) de {total_eval} sorteos.")

    print("\n-----------------------------------------------------------------------------------------")
    print("ANÁLISIS INTRA-DÍA ESPECÍFICO (HORA A HORA DENTRO DEL MISMO DÍA)")
    print("-----------------------------------------------------------------------------------------")
    # Para cada sorteo del día d (1 a 12), ¿cuántas veces repite con el sorteo d-1, d-2, d-3 del mismo día?
    df['draw_num_day'] = df.groupby('fecha').cumcount() + 1
    
    # Matriz de repetición intra-día: fila = sorteo actual (2..12), col = repite con sorteo j (1..actual-1)
    intra_reps = np.zeros((12, 12))
    day_counts = np.zeros(12)
    
    for fecha, group in df.groupby('fecha'):
        day_nums = group['numero'].tolist()
        n_draws = len(day_nums)
        for i in range(n_draws):
            day_counts[i] += 1
            for j in range(i):
                if day_nums[i] == day_nums[j]:
                    intra_reps[i, j] += 1
                    
    print("Porcentaje de veces que el sorteo actual (fila) repite exactamente el animal del sorteo anterior (columna) del mismo día:")
    print("Sorteo Actual \\ Repite con: | " + " | ".join([f"Sort {j+1}" for j in range(11)]))
    print("-" * 105)
    for i in range(1, 12):
        row_str = f"Sorteo {i+1:2d} (Hora {i+1})      | "
        cols = []
        for j in range(i):
            pct = (intra_reps[i, j] / day_counts[i]) * 100 if day_counts[i] > 0 else 0
            cols.append(f"{pct:5.2f}%")
        row_str += " | ".join(cols)
        print(row_str)

if __name__ == "__main__":
    analyze_lags()
