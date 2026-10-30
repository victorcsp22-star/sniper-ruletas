import numpy as np
import pandas as pd

def detailed_cross_comparison():
    configs = [
        ("Lotto Activo", "lotto_activo_2anios.csv", 38, 30.0),
        ("La Granjita", "la_granjita_2anios.csv", 38, 30.0),
        ("Ruleta Royal", "ruleta_royal_2anios.csv", 37, 30.0),
        ("Guacharo Activo (Pago 60x)", "guacharo_activo_2anios.csv", 77, 60.0),
        ("Guacharo Activo (Pago 65x)", "guacharo_activo_2anios.csv", 77, 65.0),
    ]

    lags = [14, 15, 18, 20]
    
    print("============================================================================================================")
    print(" REPORTE COMPARATIVO FINAL: 4 RULETAS DE ANIMALITOS (2 AÑOS DE HISTORIAL)")
    print("============================================================================================================\n")

    for name, filename, k_universe, payout in configs:
        df = pd.read_csv(filename, encoding='utf-8-sig', dtype={'numero': str})
        df['sort_key'] = pd.to_datetime(df['fecha'] + ' ' + df['hora'], format='%Y-%m-%d %I:%M %p', errors='coerce')
        df = df.sort_values(by='sort_key').reset_index(drop=True)
        total_draws = len(df)
        p0 = 1.0 / k_universe
        be_winrate = (1.0 / payout) * 100
        
        # 1. Metricas de anomalia
        l1 = (df['numero'] == df['numero'].shift(1)).sum() / (total_draws - 1) * 100
        l2 = (df['numero'] == df['numero'].shift(2)).sum() / (total_draws - 2) * 100
        l20 = (df['numero'] == df['numero'].shift(20)).sum() / (total_draws - 20) * 100
        
        # 2. Backtest Gatillo Post-Fallo 1
        cesta_hits = []
        cesta_costs = []
        for i in range(25, total_draws):
            actual = df['numero'].iloc[i]
            rec6 = set(df['numero'].iloc[i-6:i])
            cands = list({df['numero'].iloc[i-l] for l in lags} - rec6)
            hit = (actual in cands)
            cesta_hits.append(hit)
            cesta_costs.append(len(cands))
            
        bets_g1 = 0
        hits_g1 = 0
        pnl_g1 = 0.0
        streak = 0
        bankroll = 100.0
        bet_frac = 0.005 # 0.5% por animal
        peak = 0.0
        max_dd = 0.0
        
        for idx in range(len(cesta_hits)):
            hit = cesta_hits[idx]
            cost = cesta_costs[idx]
            
            if streak == 1 and cost > 0:
                bets_g1 += cost
                if hit:
                    hits_g1 += 1
                    pnl_g1 += (payout - cost)
                else:
                    pnl_g1 -= cost
                    
                bet_anim = bankroll * bet_frac
                c_comp = bet_anim * cost
                if hit:
                    bankroll += (bet_anim * payout - c_comp)
                else:
                    bankroll -= c_comp
                    
                if pnl_g1 > peak:
                    peak = pnl_g1
                dd = peak - pnl_g1
                if dd > max_dd:
                    max_dd = dd

            if hit:
                streak = 0
            else:
                streak += 1
                
        roi = (pnl_g1 / bets_g1 * 100) if bets_g1 > 0 else 0
        wr = (hits_g1 / (bets_g1 / (np.mean(cesta_costs) if np.mean(cesta_costs)>0 else 1)) * 100) if bets_g1 > 0 else 0
        
        print(f"[{name.upper()}]")
        print(f"  • Muestra analizada:          {total_draws:,} sorteos | {k_universe} opciones | Pago: {payout:.0f}x")
        print(f"  • Probabilidad teórica:       {p0*100:.2f}% | Umbral Break-Even: {be_winrate:.2f}%")
        print(f"  • Supresión Lag 1 (Inmediato): {l1:.2f}% (Déficit de {(1-l1/(p0*100))*100:.1f}% vs azar puro)")
        print(f"  • Supresión Lag 2 (2 turnos):  {l2:.2f}%")
        print(f"  • Pico de Rebote Lag 20:      {l20:.2f}%")
        print(f"  • Estrategia Gatillo 1:")
        print(f"      - Apuestas: {bets_g1:,} fichas | Aciertos: {hits_g1}")
        print(f"      - PnL Neto Plano: {pnl_g1:+.0f} unidades")
        print(f"      - Retorno (ROI):  {roi:+.2f}%")
        print(f"      - Drawdown Máx:   {max_dd:.0f} unidades")
        print(f"      - Capital Final Compuesto ($100 Inicial): ${bankroll:,.2f} USD")
        print()

if __name__ == "__main__":
    detailed_cross_comparison()
