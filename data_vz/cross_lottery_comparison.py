import numpy as np
import pandas as pd
from scipy import stats

def analyze_and_compare_all():
    lotteries = [
        ("Lotto Activo", "lotto_activo_2anios.csv"),
        ("La Granjita", "la_granjita_2anios.csv"),
        ("Ruleta Royal", "ruleta_royal_2anios.csv"),
        ("Guacharo Activo", "guacharo_activo_2anios.csv")
    ]
    
    payout = 30.0
    lags = [14, 15, 18, 20]
    
    summary_results = []
    lag_rep_summary = {}

    print("====================================================================================================")
    print(" ANÁLISIS COMPARATIVO MULTI-RULETA: LOTTO ACTIVO vs LA GRANJITA vs RULETA ROYAL vs GUÁCHARO ACTIVO")
    print("====================================================================================================\n")

    for lotto_name, filename in lotteries:
        df = pd.read_csv(filename, encoding='utf-8-sig', dtype={'numero': str})
        df['sort_key'] = pd.to_datetime(df['fecha'] + ' ' + df['hora'], format='%Y-%m-%d %I:%M %p', errors='coerce')
        df = df.sort_values(by='sort_key').reset_index(drop=True)
        
        total_draws = len(df)
        unique_nums = sorted(df['numero'].unique().tolist())
        k_universe = len(unique_nums)
        p0 = 1.0 / k_universe
        
        # 1. Repetición Inmediata (Lag 1)
        lag1_matches = (df['numero'] == df['numero'].shift(1)).sum()
        lag1_pct = (lag1_matches / (total_draws - 1)) * 100
        lag1_expected = (total_draws - 1) * p0
        
        # 2. Lag 2
        lag2_matches = (df['numero'] == df['numero'].shift(2)).sum()
        lag2_pct = (lag2_matches / (total_draws - 2)) * 100

        # 3. Lag 20
        lag20_matches = (df['numero'] == df['numero'].shift(20)).sum()
        lag20_pct = (lag20_matches / (total_draws - 20)) * 100
        
        lag_rep_summary[lotto_name] = {
            'total': total_draws,
            'k': k_universe,
            'p0': p0 * 100,
            'lag1_pct': lag1_pct,
            'lag2_pct': lag2_pct,
            'lag20_pct': lag20_pct
        }

        # 4. Backtest de la Cesta (Lags 14, 15, 18, 20) Filtrada (Excluyendo últimos 6)
        # Evaluamos:
        # A) Cesta continua
        # B) Gatillo Táctico Post-Fallo 1
        
        # Precomputar rondas
        cesta_hits = []
        cesta_costs = []
        
        for i in range(25, total_draws):
            actual = df['numero'].iloc[i]
            rec6 = set(df['numero'].iloc[i-6:i])
            cands = list({df['numero'].iloc[i-l] for l in lags} - rec6)
            hit = (actual in cands)
            cesta_hits.append(hit)
            cesta_costs.append(len(cands))
            
        # Simular Cesta Continua
        bets_cont = 0
        hits_cont = 0
        pnl_cont = 0.0
        
        # Simular Gatillo Post-Fallo 1
        bets_g1 = 0
        hits_g1 = 0
        pnl_g1 = 0.0
        streak = 0
        bankroll_comp = 100.0 # simulación interés compuesto de $100
        bet_frac = 0.005 # 0.5% por animal
        peak_g1 = 0.0
        max_dd_g1 = 0.0
        
        for idx in range(len(cesta_hits)):
            hit = cesta_hits[idx]
            cost = cesta_costs[idx]
            
            # Continua
            if cost > 0:
                bets_cont += cost
                if hit:
                    hits_cont += 1
                    pnl_cont += (payout - cost)
                else:
                    pnl_cont -= cost
                    
            # Gatillo 1
            if streak == 1 and cost > 0:
                bets_g1 += cost
                if hit:
                    hits_g1 += 1
                    pnl_g1 += (payout - cost)
                else:
                    pnl_g1 -= cost
                    
                # Compounding
                bet_anim = bankroll_comp * bet_frac
                c_comp = bet_anim * cost
                if hit:
                    bankroll_comp += (bet_anim * payout - c_comp)
                else:
                    bankroll_comp -= c_comp
                    
                if pnl_g1 > peak_g1:
                    peak_g1 = pnl_g1
                dd = peak_g1 - pnl_g1
                if dd > max_dd_g1:
                    max_dd_g1 = dd

            if hit:
                streak = 0
            else:
                streak += 1
                
        roi_cont = (pnl_cont / bets_cont * 100) if bets_cont > 0 else 0
        roi_g1 = (pnl_g1 / bets_g1 * 100) if bets_g1 > 0 else 0
        wr_g1 = (hits_g1 / (bets_g1 / 3.3) * 100) if bets_g1 > 0 else 0
        
        summary_results.append({
            'Lotería': lotto_name,
            'Sorteos': total_draws,
            'Números': k_universe,
            'Lag 1 (Real vs Teo)': f"{lag1_pct:.2f}% vs {p0*100:.2f}%",
            'Lag 20': f"{lag20_pct:.2f}%",
            'Gatillo PnL (Bs)': pnl_g1,
            'Gatillo ROI (%)': roi_g1,
            'Cap Final ($100)': bankroll_comp,
            'Max DD (fichas)': max_dd_g1
        })

    # Mostrar Tabla 1: Comprobación de Anomalías de Aleatoriedad
    print("--- [1] ¿TODAS TIENEN LA MISMA ANOMALÍA DE NO-REPETICIÓN? ---")
    print(f"{'Lotería':<18} | {'Sorteos':<8} | {'Opciones':<9} | {'Lag 1 (Inmediato)':<18} | {'Lag 2 (2 turnos)':<18} | {'Lag 20 (Rebote)':<16} | {'¿Manipulada?'}")
    print("-" * 108)
    for name, d in lag_rep_summary.items():
        teo = d['p0']
        l1 = d['lag1_pct']
        l2 = d['lag2_pct']
        l20 = d['lag20_pct']
        anom = "SÍ (Aversión masiva)" if l1 < teo * 0.5 else "No"
        print(f"{name:<18} | {d['total']:<8,} | {d['k']:<9} | {l1:>5.2f}% (Teo: {teo:.2f}%)  | {l2:>5.2f}% (Teo: {teo:.2f}%)  | {l20:>5.2f}% (Teo: {teo:.2f}%)  | {anom}")
    print()

    # Mostrar Tabla 2: Rendimiento de la Estrategia Ganadora en Cada Ruleta
    print("--- [2] COMPARATIVA DE RENTABILIDAD: GATILLO TÁCTICO POST-FALLO 1 ---")
    print(f"{'Lotería':<18} | {'Apuestas':<10} | {'PnL Neto':<12} | {'ROI (%)':<9} | {'Max DD':<9} | {'Cap Final ($100 Inicial)':<25}")
    print("-" * 108)
    for r in summary_results:
        print(f"{r['Lotería']:<18} | {r['Sorteos']:<10,} | {r['Gatillo PnL (Bs)']:>+10.0f} Bs | {r['Gatillo ROI (%)']:>+7.2f}% | {r['Max DD (fichas)']:>6.0f} f. | ${r['Cap Final ($100)']:>15,.2f} USD")
    print("=" * 108)

if __name__ == "__main__":
    analyze_and_compare_all()
