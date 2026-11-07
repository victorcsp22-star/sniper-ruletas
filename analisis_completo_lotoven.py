import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import os
import sys

def run_analysis(csv_path, output_dir):
    print("="*70)
    print("AUDITORÍA CUANTITATIVA Y ESTUDIO ESTADÍSTICO INSTITUCIONAL")
    print("LOTERÍA: LOTTO ACTIVO RD INTERNACIONAL (LOTOVEN)")
    print("="*70)
    
    if not os.path.exists(csv_path):
        print(f"Error: No se encontró el archivo {csv_path}")
        return
        
    df = pd.read_csv(csv_path, dtype={"numero": str})
    print(f"Registros brutos cargados: {len(df)}")
    
    # Normalización de número canónico: 0..36 y '00'
    def clean_num(x):
        s = str(x).strip()
        if s in ["0", "00"]:
            return s
        try:
            return str(int(s))
        except:
            return s

    df["numero_str"] = df["numero"].apply(clean_num)
    df["dt"] = pd.to_datetime(df["fecha"])
    
    # Eliminar duplicados exactos si los hubiera
    df = df.drop_duplicates(subset=["fecha", "hora"]).reset_index(drop=True)
    
    # Orden cronológico garantizado
    hora_order = {
        "08:30 AM": 1, "09:30 AM": 2, "10:30 AM": 3, "11:30 AM": 4,
        "12:30 PM": 5, "01:30 PM": 6, "02:30 PM": 7, "03:30 PM": 8,
        "04:30 PM": 9, "05:30 PM": 10, "06:30 PM": 11, "07:30 PM": 12
    }
    df["hora_rank"] = df["hora"].map(hora_order).fillna(99)
    df = df.sort_values(by=["dt", "hora_rank"]).reset_index(drop=True)
    
    N = len(df)
    unique_dates = df["fecha"].nunique()
    min_date = df["fecha"].min()
    max_date = df["fecha"].max()
    print(f"Muestra depurada: N = {N} sorteos")
    print(f"Rango temporal: {min_date} a {max_date} ({unique_dates} días)")
    
    # Mapeo canónico de 38 ruletas
    canon_animals = [
        "0", "00", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
        "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
        "21", "22", "23", "24", "25", "26", "27", "28", "29", "30",
        "31", "32", "33", "34", "35", "36"
    ]
    K = 38
    p_unif = 1.0 / K
    be_rate = 1.0 / 30.0  # Break-even a 30x = 3.333%
    
    # -------------------------------------------------------------
    # 1. TEST DE BONDAD DE AJUSTE (CHI-CUADRADO Y ENTROPÍA)
    # -------------------------------------------------------------
    counts = df["numero_str"].value_counts().reindex(canon_animals, fill_value=0)
    obs = counts.values
    exp = np.full(K, N / K)
    chi2_stat, p_val_chi2 = stats.chisquare(obs, exp)
    
    # Entropía de Shannon
    p_obs = obs / N
    entropy = -np.sum([p * np.log2(p) for p in p_obs if p > 0])
    max_entropy = np.log2(K)
    entropy_ratio = entropy / max_entropy * 100.0
    
    print("\n--- 1. PRUEBAS DE UNIFORMIDAD ESTADÍSTICA ---")
    print(f"Chi-cuadrado: Chi2 = {chi2_stat:.4f}, df = {K-1}, p-value = {p_val_chi2:.6f}")
    print(f"Entropía de Shannon: H(X) = {entropy:.4f} bits / {max_entropy:.4f} bits máx ({entropy_ratio:.2f}% de eficiencia)")
    if p_val_chi2 > 0.05:
        print("Veredicto Chi2: No se rechaza la hipótesis nula de uniformidad marginal (alpha=0.05).")
    else:
        print("Veredicto Chi2: Se RECHAZA la hipótesis nula; existe sesgo marginal significativo.")
        
    # -------------------------------------------------------------
    # 2. ANÁLISIS DE AUTOCORRELACIÓN Y REPETICIONES (LAGS 1 A 50)
    # -------------------------------------------------------------
    print("\n--- 2. ANÁLISIS DE AUTOCORRELACIÓN TEMPORAL (LAGS 1 A 50) ---")
    nums = df["numero_str"].values
    lag_results = []
    
    for L in range(1, 51):
        matches = np.sum(nums[L:] == nums[:-L])
        total_pairs = len(nums) - L
        rate = matches / total_pairs
        ev = (rate * 30.0) - 1.0
        # Test binomial de significancia
        p_val_binom = stats.binomtest(matches, total_pairs, p_unif, alternative='greater').pvalue
        lag_results.append({
            "lag": L, "matches": matches, "total": total_pairs,
            "rate": rate, "ev": ev, "p_val": p_val_binom
        })
        
    df_lags = pd.DataFrame(lag_results)
    top_lags = df_lags.sort_values(by="rate", ascending=False).head(10)
    print("Top 10 Lags con mayor frecuencia de acierto:")
    for _, row in top_lags.iterrows():
        print(f"  Lag {int(row['lag']):>2}: Tasa={row['rate']*100:.3f}% (Aciertos: {int(row['matches'])}/{int(row['total'])}) | EV={row['ev']*100:>+6.2f}% | p-val={row['p_val']:.5f}")
        
    # -------------------------------------------------------------
    # 3. CADENAS DE MARKOV DE PRIMER ORDEN (TRANSICIONES A -> B)
    # -------------------------------------------------------------
    print("\n--- 3. MODELO DE TRANSICIONES CONDICIONALES (MARKOV ORDER 1) ---")
    trans_counts = {}
    total_from = {}
    
    for t in range(len(nums) - 1):
        a = nums[t]
        b = nums[t+1]
        trans_counts[(a, b)] = trans_counts.get((a, b), 0) + 1
        total_from[a] = total_from.get(a, 0) + 1
        
    markov_rows = []
    for (a, b), cnt in trans_counts.items():
        n_a = total_from[a]
        rate = cnt / n_a
        ev = (rate * 30.0) - 1.0
        # Test binomial para esta transición
        p_val = stats.binomtest(cnt, n_a, p_unif, alternative='greater').pvalue
        markov_rows.append({
            "from": a, "to": b, "count": cnt, "n_from": n_a,
            "rate": rate, "ev": ev, "p_val": p_val
        })
        
    df_markov = pd.DataFrame(markov_rows)
    # Filtro Bonferroni para significancia institucional
    alpha_bonf = 0.05 / (K * K)
    sig_markov = df_markov[df_markov["p_val"] < alpha_bonf].sort_values(by="rate", ascending=False)
    print(f"Transiciones con significancia estadística formal tras ajuste Bonferroni (alpha = {alpha_bonf:.2e}): {len(sig_markov)}")
    if len(sig_markov) > 0:
        print(sig_markov.head(10)[["from", "to", "count", "n_from", "rate", "ev", "p_val"]])
    else:
        print("Ningún par supera el estricto umbral Bonferroni. Mostrando top 10 pares empíricos:")
        top_emp = df_markov[df_markov["n_from"] >= 30].sort_values(by="ev", ascending=False).head(10)
        for _, r in top_emp.iterrows():
            print(f"  {r['from']:>2} -> {r['to']:>2}: {r['count']}/{r['n_from']} ({r['rate']*100:.2f}%) | EV={r['ev']*100:>+6.2f}% | p-val={r['p_val']:.5f}")

    # -------------------------------------------------------------
    # 4. BACKTEST RIGUROSO: IN-SAMPLE (70%) Y OUT-OF-SAMPLE (30%)
    # -------------------------------------------------------------
    print("\n--- 4. PROTOCOLO DE BACKTEST INSTITUCIONAL (WALK-FORWARD) ---")
    split_idx = int(N * 0.70)
    train_nums = nums[:split_idx]
    test_nums = nums[split_idx:]
    print(f"Partición In-Sample (Entrenamiento): {len(train_nums)} sorteos ({df['fecha'].iloc[0]} a {df['fecha'].iloc[split_idx-1]})")
    print(f"Partición Out-of-Sample (Validación Ciega): {len(test_nums)} sorteos ({df['fecha'].iloc[split_idx]} a {df['fecha'].iloc[-1]})")
    
    # Aprender Lags ganadores en In-Sample
    in_lags = []
    for L in range(1, 40):
        m = np.sum(train_nums[L:] == train_nums[:-L])
        tot = len(train_nums) - L
        r = m / tot
        p = stats.binomtest(m, tot, p_unif, alternative='greater').pvalue
        if r > be_rate and p < 0.05: # Edge estadístico real in-sample
            in_lags.append(L)
            
    print(f"Lags con ventaja estadística in-sample (+EV con p < 0.05): {in_lags}")
    
    # Aprender Pares Markov ganadores en In-Sample
    in_trans = {}
    in_tot = {}
    for t in range(len(train_nums) - 1):
        a = train_nums[t]
        b = train_nums[t+1]
        in_trans[(a, b)] = in_trans.get((a, b), 0) + 1
        in_tot[a] = in_tot.get(a, 0) + 1
        
    in_markov_pairs = set()
    for (a, b), cnt in in_trans.items():
        n_a = in_tot[a]
        if n_a >= 25:
            r = cnt / n_a
            p = stats.binomtest(cnt, n_a, p_unif, alternative='greater').pvalue
            if r > be_rate and p < 0.05:
                in_markov_pairs.add((a, b))
                
    print(f"Pares Markov identificados in-sample con p < 0.05: {len(in_markov_pairs)}")
    
    # SIMULACIÓN OUT-OF-SAMPLE
    # 1. Estrategia Lags In-Sample
    # 2. Estrategia Markov In-Sample
    # 3. Estrategia Base (Ruleta aleatoria / House baseline)
    
    equity_lags = [0.0]
    equity_markov = [0.0]
    equity_baseline = [0.0]
    
    bets_lags = 0
    wins_lags = 0
    bets_markov = 0
    wins_markov = 0
    
    # Historial para mirar hacia atrás en el test
    full_history = list(train_nums)
    
    for i, actual in enumerate(test_nums):
        # 1. Evaluar Lags
        for L in in_lags:
            if len(full_history) >= L:
                pred = full_history[-L]
                bets_lags += 1
                if pred == actual:
                    wins_lags += 1
                    equity_lags.append(equity_lags[-1] + 29.0)
                else:
                    equity_lags.append(equity_lags[-1] - 1.0)
                    
        # 2. Evaluar Markov
        prev = full_history[-1]
        # Si el previo tiene un par validado
        markov_candidates = [b for (a, b) in in_markov_pairs if a == prev]
        for pred in markov_candidates:
            bets_markov += 1
            if pred == actual:
                wins_markov += 1
                equity_markov.append(equity_markov[-1] + 29.0)
            else:
                equity_markov.append(equity_markov[-1] - 1.0)
                
        # 3. Baseline (1 apuesta aleatoria por sorteo)
        pred_base = np.random.choice(canon_animals)
        if pred_base == actual:
            equity_baseline.append(equity_baseline[-1] + 29.0)
        else:
            equity_baseline.append(equity_baseline[-1] - 1.0)
            
        full_history.append(actual)
        
    def get_metrics(eq_curve, bets, wins):
        if bets == 0:
            return {"bets": 0, "wins": 0, "win_rate": 0, "net_pnl": 0, "roi": 0, "pf": 0, "mdd": 0}
        net = eq_curve[-1]
        roi = net / bets * 100.0
        gross_profit = wins * 29.0
        gross_loss = (bets - wins) * 1.0
        pf = (gross_profit / gross_loss) if gross_loss > 0 else np.nan
        # Max Drawdown
        arr = np.array(eq_curve)
        peaks = np.maximum.accumulate(arr)
        dds = peaks - arr
        mdd = np.max(dds)
        return {
            "bets": bets, "wins": wins, "win_rate": (wins/bets)*100.0,
            "net_pnl": net, "roi": roi, "pf": pf, "mdd": mdd
        }
        
    met_lags = get_metrics(equity_lags, bets_lags, wins_lags)
    met_markov = get_metrics(equity_markov, bets_markov, wins_markov)
    met_base = get_metrics(equity_baseline, len(test_nums), int(sum(1 for e in np.diff(equity_baseline) if e > 0)))
    
    print("\n--- RESULTADOS ESTRICTOS OUT-OF-SAMPLE (DATOS NUNCA ANTES VISTOS) ---")
    print(f"Punto de Equilibrio Teórico (Break-even): 3.333% de aciertos | Retorno Casa: -21.05%")
    print(f"ESTRATEGIA 1 (Top Lags OOS):")
    print(f"  Apuestas: {met_lags['bets']} | Aciertos: {met_lags['wins']} | Tasa de Acierto: {met_lags['win_rate']:.3f}%")
    print(f"  PnL Neto: {met_lags['net_pnl']:+.1f} uds | ROI: {met_lags['roi']:+.2f}% | Profit Factor: {met_lags['pf']:.2f} | Max DD: {met_lags['mdd']:.1f} uds")
    print(f"ESTRATEGIA 2 (Top Markov OOS):")
    print(f"  Apuestas: {met_markov['bets']} | Aciertos: {met_markov['wins']} | Tasa de Acierto: {met_markov['win_rate']:.3f}%")
    print(f"  PnL Neto: {met_markov['net_pnl']:+.1f} uds | ROI: {met_markov['roi']:+.2f}% | Profit Factor: {met_markov['pf']:.2f} | Max DD: {met_markov['mdd']:.1f} uds")
    print(f"BASELINE RANDOM (Control OOS):")
    print(f"  Apuestas: {met_base['bets']} | Tasa de Acierto: {met_base['win_rate']:.3f}% | PnL Neto: {met_base['net_pnl']:+.1f} uds | ROI: {met_base['roi']:+.2f}% | Profit Factor: {met_base['pf']:.2f}")

    # -------------------------------------------------------------
    # 5. GENERACIÓN DE GRÁFICO AUDITABLE
    # -------------------------------------------------------------
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f"Auditoría Cuantitativa Institucional: Lotto Activo RD Internacional\n(Base de Datos Completa Lotoven: N={N} sorteos, {min_date} a {max_date})", fontsize=15, fontweight='bold')
    
    # Subplot 1: Frecuencia Marginal de los 38 Animalitos
    ax1 = axes[0, 0]
    x_idx = np.arange(K)
    ax1.bar(x_idx, obs, color='#1f77b4', alpha=0.8, edgecolor='black', label='Observado')
    ax1.axhline(exp[0], color='red', linestyle='--', linewidth=2, label=f'Esperado Teórico ({exp[0]:.1f})')
    ax1.set_xticks(x_idx)
    ax1.set_xticklabels(canon_animals, rotation=90, fontsize=8)
    ax1.set_title(f"Distribución Marginal (Chi2={chi2_stat:.2f}, p={p_val_chi2:.4f})", fontweight='bold')
    ax1.set_ylabel("Frecuencia Absoluta")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Subplot 2: Lags 1 a 35 vs Break-even
    ax2 = axes[0, 1]
    lags_plot = df_lags[df_lags["lag"] <= 35]
    ax2.plot(lags_plot["lag"], lags_plot["rate"] * 100.0, marker='o', color='#2ca02c', linewidth=2, label='Tasa de Acierto Empírica (%)')
    ax2.axhline(be_rate * 100.0, color='red', linestyle='--', linewidth=2, label=f'Break-even 30x ({be_rate*100:.2f}%)')
    ax2.axhline(p_unif * 100.0, color='blue', linestyle=':', linewidth=1.5, label=f'Esperanza Teórica 1/38 ({p_unif*100:.2f}%)')
    ax2.set_title("Estructura de Autocorrelación por Retardo (Lags 1 a 35)", fontweight='bold')
    ax2.set_xlabel("Lag (Retardo)")
    ax2.set_ylabel("Tasa de Acierto (%)")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Subplot 3: Curvas de Capital Out-of-Sample
    ax3 = axes[1, 0]
    if len(equity_lags) > 1:
        ax3.plot(equity_lags, label=f'Top Lags OOS (PF={met_lags["pf"]:.2f}, ROI={met_lags["roi"]:+.1f}%)', color='#2ca02c', linewidth=1.8)
    if len(equity_markov) > 1:
        ax3.plot(equity_markov, label=f'Top Markov OOS (PF={met_markov["pf"]:.2f}, ROI={met_markov["roi"]:+.1f}%)', color='#9467bd', linewidth=1.8)
    ax3.plot(equity_baseline, label=f'Control Aleatorio (ROI={met_base["roi"]:+.1f}%)', color='#d62728', linestyle='--', alpha=0.7)
    ax3.axhline(0, color='black', linewidth=1)
    ax3.set_title("Validación Fuera de Muestra (Out-of-Sample Cumulative PnL)", fontweight='bold')
    ax3.set_xlabel("Número de Apuestas")
    ax3.set_ylabel("PnL Neto (Unidades)")
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Subplot 4: Drawdowns Out-of-Sample
    ax4 = axes[1, 1]
    if len(equity_lags) > 1:
        arr_lags = np.array(equity_lags)
        pk_lags = np.maximum.accumulate(arr_lags)
        dd_lags = pk_lags - arr_lags
        ax4.plot(dd_lags, label=f'Drawdown Lags (Max={met_lags["mdd"]:.0f} u)', color='#2ca02c', alpha=0.8)
    if len(equity_markov) > 1:
        arr_m = np.array(equity_markov)
        pk_m = np.maximum.accumulate(arr_m)
        dd_m = pk_m - arr_m
        ax4.plot(dd_m, label=f'Drawdown Markov (Max={met_markov["mdd"]:.0f} u)', color='#9467bd', alpha=0.8)
    ax4.set_title("Curva de Drawdown Out-of-Sample", fontweight='bold')
    ax4.set_xlabel("Número de Apuestas")
    ax4.set_ylabel("Profundidad de Caída (Unidades)")
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    chart_path = os.path.join(output_dir, "grafica_backtest_lotoven_lotto_activo_rd.png")
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"\nGráfica institucional generada exitosamente en: {chart_path}")
    
    return {
        "N": N, "min_date": min_date, "max_date": max_date,
        "chi2": chi2_stat, "p_chi2": p_val_chi2,
        "entropy": entropy, "entropy_ratio": entropy_ratio,
        "met_lags": met_lags, "met_markov": met_markov, "met_base": met_base
    }

if __name__ == "__main__":
    csv_file = "C:/Users/victo/nuevas_ruletas/lotto_activo_rd_lotoven_completo.csv"
    out_dir = "C:/Users/victo/.gemini/antigravity/brain/da61199f-f45d-4b1d-bcd9-a17212f844b0"
    run_analysis(csv_file, out_dir)
