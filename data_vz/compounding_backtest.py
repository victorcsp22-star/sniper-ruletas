import numpy as np
import pandas as pd

def run_compounding_backtest():
    csv_path = r"C:\Users\victo\.gemini\antigravity\scratch\lotto_activo_bot\lotto_activo_2anios.csv"
    df = pd.read_csv(csv_path, encoding='utf-8-sig', dtype={'numero': str})
    df['sort_key'] = pd.to_datetime(df['fecha'] + ' ' + df['hora'], format='%Y-%m-%d %I:%M %p', errors='coerce')
    df = df.sort_values(by='sort_key').reset_index(drop=True)
    
    total = len(df)
    payout = 30.0
    start_idx = 25
    lags = [14, 15, 18, 20]

    # Precomputar el historial virtual de la Cesta 4 filtrada
    rounds = []
    streak = 0
    
    for i in range(start_idx, total):
        actual = df['numero'].iloc[i]
        rec6 = set(df['numero'].iloc[i-6:i])
        cands = list({df['numero'].iloc[i-l] for l in lags} - rec6)
        hit = (actual in cands)
        n_cands = len(cands)
        
        rounds.append({
            'index': i,
            'fecha': df['fecha'].iloc[i],
            'hora': df['hora'].iloc[i],
            'streak_before': streak,
            'n_cands': n_cands,
            'hit': hit
        })
        
        if hit:
            streak = 0
        else:
            streak += 1

    print("=========================================================================================")
    print(" BACKTEST CON INTERÉS COMPUESTO (REINVERSIÓN): DE 0.10 $ AL DÍA DE HOY")
    print("=========================================================================================\n")

    # Analizaremos las dos mejores estrategias:
    # 1. Estrategia A: Gatillo Táctico Post-Fallo 1 (La más segura y explosiva en ROI)
    # 2. Estrategia B: Salto de Zona Fría (La de mayor volumen de juego continuo)

    # Definir Capital Inicial y Regla de Reinversión Proporcional:
    # Si la apuesta inicial por animal es 0.10 $, el gasto por tiro es de ~0.30 $ a 0.40 $.
    # Para sobrevivir con holgura al drawdown histórico (131 unidades en Gatillo 1, o 583 en Zona Fría):
    # - En Gatillo 1: 131 unidades a 0.10 $ = 13.10 $ de drawdown máximo.
    #   Un capital inicial de 20.00 $ a 50.00 $ es realista y prudente.
    # - Regla de reinversión: La apuesta por animal escala proporcionalmente al capital:
    #   bet_per_animal(t) = current_bankroll * (0.10 / initial_bankroll)
    #   (por ejemplo, si el capital se duplica a 40 $, la apuesta sube a 0.20 $; si sube a 200 $, sube a 1.00 $).

    scenarios = [
        # (Nombre Estrategia, Filtro Gatillo, Capital Inicial, Apuesta Inicial por Animal)
        ("1. Gatillo Post-Fallo 1 (Capital Inicial $20 - Apuesta base 0.5% por animal)", lambda r: r['streak_before'] == 1, 20.0, 0.10),
        ("2. Gatillo Post-Fallo 1 (Capital Inicial $30 - Apuesta base 0.33% por animal)", lambda r: r['streak_before'] == 1, 30.0, 0.10),
        ("3. Gatillo Post-Fallo 1 (Capital Inicial $50 - Apuesta base 0.20% por animal)", lambda r: r['streak_before'] == 1, 50.0, 0.10),
        ("4. Salto de Zona Fría  (Capital Inicial $100 - Apuesta base 0.10% por animal)", lambda r: r['streak_before'] not in [3, 4, 5, 6], 100.0, 0.10),
    ]

    for title, cond_fn, init_bankroll, init_bet in scenarios:
        bankroll = init_bankroll
        bet_fraction = init_bet / init_bankroll # fracción por animal
        peak = init_bankroll
        max_dd_pct = 0.0
        max_dd_usd = 0.0
        
        bets_count = 0
        hits_count = 0
        total_staked = 0.0
        
        history_equity = []
        history_dates = []
        
        for r in rounds:
            if cond_fn(r) and r['n_cands'] > 0:
                # Tamaño de apuesta por animal con reinversión
                # Nunca menor a 0.10 $, pero proporcional al capital actual
                bet_per_animal = bankroll * bet_fraction
                total_cost = bet_per_animal * r['n_cands']
                
                # Proteger contra bancarrota
                if total_cost >= bankroll:
                    total_cost = bankroll * 0.99
                    bet_per_animal = total_cost / r['n_cands']
                    
                total_staked += total_cost
                bets_count += 1
                
                if r['hit']:
                    hits_count += 1
                    # Pago: 30x por cada 1 apostado al animal ganador
                    win_amount = bet_per_animal * payout
                    bankroll += (win_amount - total_cost)
                else:
                    bankroll -= total_cost
                    
                if bankroll > peak:
                    peak = bankroll
                dd_usd = peak - bankroll
                dd_pct = (dd_usd / peak) * 100 if peak > 0 else 0
                if dd_pct > max_dd_pct:
                    max_dd_pct = dd_pct
                if dd_usd > max_dd_usd:
                    max_dd_usd = dd_usd
                    
                history_equity.append(bankroll)
                history_dates.append(r['fecha'])

        net_profit = bankroll - init_bankroll
        mult = bankroll / init_bankroll
        cagr = (mult ** (1.0 / 2.0) - 1.0) * 100 # rendimiento anualizado compuesto

        print("=" * 95)
        print(f" {title.upper()}")
        print("=" * 95)
        print(f"• Capital Inicial:             ${init_bankroll:.2f} USD")
        print(f"• Apuesta inicial por animal:  ${init_bet:.2f} USD ({bet_fraction*100:.2f}% del capital)")
        print(f"• Sorteos jugados con dinero:  {bets_count:,} sorteos")
        print(f"• Aciertos conseguidos:        {hits_count:,} (Win Rate: {hits_count/bets_count*100:.2f}%)")
        print(f"• Capital Final (Hoy):         ${bankroll:,.2f} USD")
        print(f"• Ganancia Neta:               +${net_profit:,.2f} USD")
        print(f"• Multiplicador del Capital:   {mult:,.2f}x (Multiplicó por {mult:,.1f})")
        print(f"• Rentabilidad Anualizada:     +{cagr:,.1f}% anual compuesto")
        print(f"• Drawdown Máximo:             -{max_dd_pct:.2f}% (-${max_dd_usd:,.2f} USD)")
        
        # Evolución semestral
        df_hist = pd.DataFrame({'fecha': history_dates, 'equity': history_equity})
        df_hist['fecha_dt'] = pd.to_datetime(df_hist['fecha'])
        df_hist = df_hist.set_index('fecha_dt')
        resample_6m = df_hist['equity'].resample('6ME').last().dropna()
        
        print("\n  Progreso del Capital a lo largo del tiempo:")
        print(f"    - Inicio (Sept 2024):       ${init_bankroll:>10,.2f} USD (Apuesta: ${init_bet:.2f} / animal)")
        for date_val, val in resample_6m.items():
            curr_bet = val * bet_fraction
            print(f"    - {date_val.strftime('%B %Y'):<25}: ${val:>10,.2f} USD (Apuesta actual: ${curr_bet:.2f} / animal)")
        print()

if __name__ == "__main__":
    run_compounding_backtest()
