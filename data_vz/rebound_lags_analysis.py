import numpy as np
import pandas as pd
from scipy import stats

def analyze_rebound_lags():
    lotteries = [
        ("La Granjita", "la_granjita_2anios.csv", 38, 30.0, 40),
        ("Ruleta Royal", "ruleta_royal_2anios.csv", 37, 30.0, 40),
        ("Guacharo Activo", "guacharo_activo_2anios.csv", 77, 60.0, 50)
    ]
    
    print("=========================================================================================")
    print(" ANÁLISIS EXHAUSTIVO DEL EFECTO REBOTE: LAGS PREFERIDOS Y PICOS ANORMALES")
    print("=========================================================================================\n")

    for name, filename, k_universe, payout, max_lag in lotteries:
        df = pd.read_csv(filename, encoding='utf-8-sig', dtype={'numero': str})
        df['sort_key'] = pd.to_datetime(df['fecha'] + ' ' + df['hora'], format='%Y-%m-%d %I:%M %p', errors='coerce')
        df = df.sort_values(by='sort_key').reset_index(drop=True)
        
        nums = df['numero'].tolist()
        total = len(nums)
        p0 = 1.0 / k_universe
        be_winrate = (1.0 / payout) * 100
        
        lag_stats = []
        for lag in range(1, max_lag + 1):
            valid = total - lag
            # Pure python fast list matches
            matches = sum(1 for i in range(lag, total) if nums[i] == nums[i-lag])
            p_hat = matches / valid
            se = np.sqrt(p0 * (1.0 - p0) / valid)
            z = (p_hat - p0) / se
            p_val = 2.0 * (1.0 - stats.norm.cdf(abs(z)))
            
            # Filtrado excluyendo últimos 6
            matches_filt = 0
            trials_filt = 0
            start_i = max(25, lag)
            for i in range(start_i, total):
                cand = nums[i-lag]
                # ultimos 6
                rec6 = set(nums[i-6:i])
                if cand not in rec6:
                    trials_filt += 1
                    if nums[i] == cand:
                        matches_filt += 1
            p_filt = (matches_filt / trials_filt * 100) if trials_filt > 0 else 0
            
            lag_stats.append({
                'lag': lag,
                'matches': matches,
                'valid': valid,
                'pct': p_hat * 100,
                'pct_filt': p_filt,
                'z': z,
                'p_val': p_val
            })
            
        df_lags = pd.DataFrame(lag_stats)
        
        # Identificar Top Lags con Mayor Exceso Positivo (Rebote)
        df_rebound = df_lags.sort_values(by='z', ascending=False).reset_index(drop=True)
        
        print("=" * 95)
        print(f" {name.upper()} ({k_universe} animales | Azar Teórico: {p0*100:.2f}% | Break-Even: {be_winrate:.2f}%)")
        print("=" * 95)
        print(f"• Total sorteos analizados: {total:,}")
        print("\nTOP 8 LAGS CON MAYOR EFECTO REBOTE (PICOS MÁS ALTOS DE REAPARICIÓN):")
        print(f"{'Ranking':<8} | {'Lag (Distancia)':<20} | {'Prob. Bruta':<12} | {'Prob. Filtrada':<15} | {'Z-Score':<8} | {'Valor p':<8} | {'Supera Break-Even?'}")
        print("-" * 95)
        
        for rank, row in df_rebound.head(8).iterrows():
            lag_num = int(row['lag'])
            horas_aprox = lag_num
            dias_aprox = lag_num / 12.0
            tiempo_str = f"Lag {lag_num} (~{horas_aprox}h / {dias_aprox:.1f}d)"
            
            supera = "SI (+EV)" if row['pct_filt'] > be_winrate else ("Cerca" if row['pct_filt'] > be_winrate * 0.95 else "No")
            print(f"#{rank+1:<7} | {tiempo_str:<20} | {row['pct']:>6.2f}%      | {row['pct_filt']:>6.2f}%         | {row['z']:>+6.2f} | {row['p_val']:>6.4f} | {supera}")
            
        # Evaluar la Cesta a Medida con sus 4 mejores Lags
        top_4_lags = df_rebound.head(4)['lag'].tolist()
        print(f"\n>> Cesta Óptima Personalizada para {name}: Lags {top_4_lags}")
        
        # Test rápido del Gatillo 1 con la cesta personalizada
        pnl_custom = 0.0
        bets_custom = 0
        hits_custom = 0
        streak = 0
        bankroll = 100.0
        
        start_eval = max(top_4_lags) + 6
        for i in range(start_eval, total):
            actual = nums[i]
            rec6 = set(nums[i-6:i])
            cands = list({nums[i-l] for l in top_4_lags} - rec6)
            hit = (actual in cands)
            cost = len(cands)
            
            if streak == 1 and cost > 0:
                bets_custom += cost
                if hit:
                    hits_custom += 1
                    pnl_custom += (payout - cost)
                else:
                    pnl_custom -= cost
                    
                bet_anim = bankroll * 0.005
                c_comp = bet_anim * cost
                if hit:
                    bankroll += (bet_anim * payout - c_comp)
                else:
                    bankroll -= c_comp
                    
            if hit:
                streak = 0
            else:
                streak += 1
                
        roi_custom = (pnl_custom / bets_custom * 100) if bets_custom > 0 else 0
        print(f"   Rendimiento Gatillo 1 con Lags Personalizados {top_4_lags}:")
        print(f"   -> Apuestas: {bets_custom:,} fichas | Aciertos: {hits_custom}")
        print(f"   -> PnL Plano: {pnl_custom:+.0f} unidades | ROI: {roi_custom:+.2f}%")
        print(f"   -> Capital Final Compuesto ($100 Inicial): ${bankroll:,.2f} USD\n")

if __name__ == "__main__":
    analyze_rebound_lags()
