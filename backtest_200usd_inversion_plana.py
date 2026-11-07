import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import os

def run_flat_backtest():
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
    
    N = len(df)
    canon_animals = [
        "0", "00", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
        "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
        "21", "22", "23", "24", "25", "26", "27", "28", "29", "30",
        "31", "32", "33", "34", "35", "36"
    ]
    
    # 70% In-Sample para descubrimiento de pares Markov afines
    split_idx = int(N * 0.70)
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]
    
    trans = {}
    tot = {}
    for i in range(len(train_df) - 1):
        a = train_df["numero"].iloc[i]
        b = train_df["numero"].iloc[i+1]
        trans[(a, b)] = trans.get((a, b), 0) + 1
        tot[a] = tot.get(a, 0) + 1
        
    candidate_pairs = {}
    for (a, b), cnt in trans.items():
        if tot[a] >= 30:
            r = cnt / tot[a]
            p = stats.binomtest(cnt, tot[a], 1/38, alternative='greater').pvalue
            if r > 1/30 and p < 0.05:
                if a not in candidate_pairs:
                    candidate_pairs[a] = []
                candidate_pairs[a].append(b)
                
    # Evaluamos 4 variantes de inversión plana con $200 de capital inicial y $1 por apuesta
    # 1. Estrategia A: Markov + Fresh Tardío (Sorteos >= 10: 05:30 PM, 06:30 PM, 07:30 PM)
    # 2. Estrategia B: Markov + Fresh Final (Sorteos >= 11: 06:30 PM, 07:30 PM)
    # 3. Estrategia C: Markov + Fresh Global (Todos los sorteos del día con filtro no salido)
    # 4. Estrategia D (Control): Apuesta aleatoria de $1 (Baseline casa)
    
    STARTING_CAPITAL = 200.0
    BET_SIZE = 1.0
    PAYOUT_MULTIPLIER = 30.0 # Paga 30x por acierto (ganancia neta +$29)
    
    def simulate_strategy(min_hour=None, use_fresh=True, is_random=False):
        cap = STARTING_CAPITAL
        cap_history = [cap]
        bets = 0
        wins = 0
        losses = 0
        current_date = None
        seen_today = set()
        
        current_streak_w = 0
        current_streak_l = 0
        max_streak_w = 0
        max_streak_l = 0
        
        ruined = False
        ruin_bet_idx = None
        
        for i in range(split_idx, len(df)):
            row = df.iloc[i]
            prev_num = df["numero"].iloc[i-1]
            actual = row["numero"]
            d = row["fecha"]
            h = row["h_rank"]
            
            if d != current_date:
                current_date = d
                seen_today = set()
                
            if is_random:
                targets = [np.random.choice(canon_animals)]
            else:
                cands = candidate_pairs.get(prev_num, [])
                if use_fresh:
                    targets = [c for c in cands if c not in seen_today]
                else:
                    targets = cands
                    
            if min_hour is not None and not is_random:
                if h < min_hour:
                    targets = []
                    
            for target in targets:
                if cap < BET_SIZE:
                    ruined = True
                    if ruin_bet_idx is None:
                        ruin_bet_idx = bets
                    break
                    
                bets += 1
                if target == actual:
                    wins += 1
                    cap += BET_SIZE * (PAYOUT_MULTIPLIER - 1.0)
                    current_streak_w += 1
                    current_streak_l = 0
                    if current_streak_w > max_streak_w: max_streak_w = current_streak_w
                else:
                    losses += 1
                    cap -= BET_SIZE
                    current_streak_l += 1
                    current_streak_w = 0
                    if current_streak_l > max_streak_l: max_streak_l = current_streak_l
                    
                cap_history.append(cap)
                
            seen_today.add(actual)
            
        arr = np.array(cap_history)
        peaks = np.maximum.accumulate(arr)
        dds = peaks - arr
        mdd_dollars = np.max(dds)
        mdd_pct = (mdd_dollars / np.max(peaks)) * 100.0 if np.max(peaks) > 0 else 0
        
        win_rate = (wins / bets * 100.0) if bets > 0 else 0
        gross_profit = wins * BET_SIZE * (PAYOUT_MULTIPLIER - 1.0)
        gross_loss = losses * BET_SIZE
        pf = (gross_profit / gross_loss) if gross_loss > 0 else 0
        net_profit = cap - STARTING_CAPITAL
        roi = (net_profit / (bets * BET_SIZE) * 100.0) if bets > 0 else 0
        
        return {
            "cap_history": cap_history,
            "final_cap": cap,
            "net_profit": net_profit,
            "bets": bets,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "roi": roi,
            "pf": pf,
            "mdd_dollars": mdd_dollars,
            "mdd_pct": mdd_pct,
            "max_streak_w": max_streak_w,
            "max_streak_l": max_streak_l,
            "ruined": ruined,
            "ruin_bet_idx": ruin_bet_idx
        }

    res_tardio10 = simulate_strategy(min_hour=10, use_fresh=True)
    res_final11 = simulate_strategy(min_hour=11, use_fresh=True)
    res_global = simulate_strategy(min_hour=None, use_fresh=True)
    res_control = simulate_strategy(is_random=True)
    
    print("="*75)
    print("BACKTEST CON INVERSIÓN PLANA ($200 USD CAPITAL INICIAL)")
    print(f"Apuesta fija: $1.00 USD por selección | Pago banca: 30x (+29 unidades)")
    print(f"Período Out-of-Sample: 5,789 sorteos ({test_df['fecha'].iloc[0]} a {test_df['fecha'].iloc[-1]})")
    print("="*75)
    
    strats = [
        ("Markov + Fresh Tardío (Sorteos >= 10: 05:30-07:30 PM)", res_tardio10),
        ("Markov + Fresh Final  (Sorteos >= 11: 06:30-07:30 PM)", res_final11),
        ("Markov + Fresh Global (Todos los sorteos del día)   ", res_global),
        ("Control Aleatorio (Baseline Casa - Rastrillo 21%)   ", res_control)
    ]
    
    for name, r in strats:
        print(f"\n>>> {name}")
        print(f"  Capital Inicial:   ${STARTING_CAPITAL:.2f} USD")
        print(f"  Capital Final:     ${r['final_cap']:.2f} USD  ({r['net_profit']:+.2f} USD)")
        print(f"  Retorno (ROI):     {r['roi']:+.2f}% sobre volumen apostado")
        print(f"  Total Apuestas:    {r['bets']}  (Aciertos: {r['wins']}, Fallos: {r['losses']})")
        print(f"  Tasa de Acierto:   {r['win_rate']:.3f}% (Break-even necesario: 3.333%)")
        print(f"  Profit Factor:     {r['pf']:.2f}")
        print(f"  Max Drawdown:      ${r['mdd_dollars']:.2f} USD ({r['mdd_pct']:.2f}% de la cuenta)")
        print(f"  Racha Máx Pérdida: {r['max_streak_l']} fallos consecutivos")
        print(f"  Racha Máx Victoria:{r['max_streak_w']} aciertos consecutivos")
        print(f"  ¿Bancarrota (<$1)? {'SÍ (en apuesta ' + str(r['ruin_bet_idx']) + ')' if r['ruined'] else 'NO (Supervivencia 100%)'}")

    # Gráfico Institucional
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [2.2, 1]})
    fig.suptitle("Backtest con Inversión Plana ($200 Capital Inicial | Apuesta Fija: $1.00 USD)\nLotto Activo RD Internacional - Validación Ciega Out-of-Sample (5,789 Sorteos)", fontsize=13, fontweight='bold')
    
    ax1 = axes[0]
    ax1.plot(res_final11["cap_history"], label=f'Markov + Fresh Final (>=Sorteo 11): ${res_final11["final_cap"]:.2f} (+${res_final11["net_profit"]:.2f}, PF={res_final11["pf"]:.2f})', color='#2ca02c', linewidth=2.2)
    ax1.plot(res_tardio10["cap_history"], label=f'Markov + Fresh Tardío (>=Sorteo 10): ${res_tardio10["final_cap"]:.2f} (+${res_tardio10["net_profit"]:.2f}, PF={res_tardio10["pf"]:.2f})', color='#1f77b4', linewidth=2)
    ax1.plot(res_global["cap_history"], label=f'Markov + Fresh Global: ${res_global["final_cap"]:.2f} (${res_global["net_profit"]:.2f}, PF={res_global["pf"]:.2f})', color='#ff7f0e', linewidth=1.5)
    ax1.plot(res_control["cap_history"], label=f'Control Aleatorio: ${res_control["final_cap"]:.2f} (${res_control["net_profit"]:.2f}) [Ruina Casa]', color='#d62728', linestyle='--', linewidth=1.5)
    
    ax1.axhline(STARTING_CAPITAL, color='black', linestyle=':', label='Capital Inicial ($200.00 USD)')
    ax1.axhline(0, color='red', linestyle='-', linewidth=0.8, alpha=0.7)
    ax1.set_title("Curva de Evolución de Capital (Balance en USD)", fontweight='bold')
    ax1.set_ylabel("Capital ($ USD)")
    ax1.legend(loc='upper left', fontsize=9.5)
    ax1.grid(True, alpha=0.3)
    
    # Subplot 2: Drawdowns
    ax2 = axes[1]
    for res, label, col in [
        (res_final11, 'Drawdown Final (>=11)', '#2ca02c'),
        (res_tardio10, 'Drawdown Tardío (>=10)', '#1f77b4'),
        (res_global, 'Drawdown Global', '#ff7f0e')
    ]:
        arr = np.array(res["cap_history"])
        pk = np.maximum.accumulate(arr)
        dd = pk - arr
        ax2.plot(dd, label=f'{label} (Max: -${res["mdd_dollars"]:.2f})', color=col, linewidth=1.3)
        
    ax2.set_title("Profundidad de Drawdown en Dólares ($ USD)", fontweight='bold')
    ax2.set_xlabel("Número de Apuestas Ejecutadas")
    ax2.set_ylabel("Drawdown ($ USD)")
    ax2.legend(loc='upper right', fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    chart_file = os.path.join(out_dir, "grafica_backtest_200usd_inversion_plana.png")
    plt.savefig(chart_file, dpi=300)
    plt.close()
    print(f"\nGráfica guardada exitosamente en: {chart_file}")

if __name__ == "__main__":
    run_flat_backtest()
