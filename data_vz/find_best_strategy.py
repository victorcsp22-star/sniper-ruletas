import numpy as np
import pandas as pd

def find_best_strategy():
    csv_path = r"C:\Users\victo\.gemini\antigravity\scratch\lotto_activo_bot\lotto_activo_2anios.csv"
    df = pd.read_csv(csv_path, encoding='utf-8-sig', dtype={'numero': str})
    df['sort_key'] = pd.to_datetime(df['fecha'] + ' ' + df['hora'], format='%Y-%m-%d %I:%M %p', errors='coerce')
    df = df.sort_values(by='sort_key').reset_index(drop=True)
    
    total = len(df)
    payout = 30.0
    start_idx = 25
    mid_idx = total // 2

    # Definir las estrategias candidatas
    # Cada estrategia es una función que recibe (i, actual, df, cur_streak) y retorna lista de candidatos a apostar
    
    def get_recent_6(i):
        return set(df['numero'].iloc[i-6:i])

    strategies = {}

    # Estrategia 1: Cesta Completa 4 Lags (14, 15, 18, 20) Filtrada
    def strat_cesta_4(i, streak):
        rec6 = get_recent_6(i)
        cands = {df['numero'].iloc[i-l] for l in [14, 15, 18, 20]}
        return list(cands - rec6)
    strategies["1. Cesta 4 (Lags 14, 15, 18, 20) Filtrada"] = strat_cesta_4

    # Estrategia 2: Dúo Armónico (Lags 18 y 20) Filtrado
    def strat_duo_18_20(i, streak):
        rec6 = get_recent_6(i)
        cands = {df['numero'].iloc[i-18], df['numero'].iloc[i-20]}
        return list(cands - rec6)
    strategies["2. Dúo Armónico (Lags 18 y 20) Filtrado"] = strat_duo_18_20

    # Estrategia 3: Sniper Lag 20 Puro Filtrado
    def strat_sniper_20(i, streak):
        rec6 = get_recent_6(i)
        c = df['numero'].iloc[i-20]
        return [c] if c not in rec6 else []
    strategies["3. Sniper Solitario Lag 20 Filtrado"] = strat_sniper_20

    # Estrategia 4: Sniper Solitario Lag 18 Filtrado
    def strat_sniper_18(i, streak):
        rec6 = get_recent_6(i)
        c = df['numero'].iloc[i-18]
        return [c] if c not in rec6 else []
    strategies["4. Sniper Solitario Lag 18 Filtrado"] = strat_sniper_18

    # Estrategia 5: Trío de Élite (Lags 14, 18, 20) Filtrado (excluye 15 que es el más débil)
    def strat_trio_14_18_20(i, streak):
        rec6 = get_recent_6(i)
        cands = {df['numero'].iloc[i-l] for l in [14, 18, 20]}
        return list(cands - rec6)
    strategies["5. Trío de Élite (Lags 14, 18, 20) Filtrado"] = strat_trio_14_18_20

    # Estrategia 6: Cesta 4 con Filtro de Pausa (Evita la 'zona fría' de pérdidas 3, 4, 5)
    # Juega tras ganar o tras 1-2 pérdidas, o tras 7+ pérdidas, pero salta turnos 3 a 6
    def strat_cesta_pausa(i, streak):
        if 3 <= streak <= 5: # Enfriamiento
            return []
        rec6 = get_recent_6(i)
        cands = {df['numero'].iloc[i-l] for l in [14, 15, 18, 20]}
        return list(cands - rec6)
    strategies["6. Cesta 4 con Pausa Táctica (Salta fallos 3 a 5)"] = strat_cesta_pausa

    # Estrategia 7: Francotirador de Rebote Rápido (Juega Cesta SOLO tras perder 1 o 2)
    def strat_cesta_post_fallo1_2(i, streak):
        if streak in [1, 2]:
            rec6 = get_recent_6(i)
            cands = {df['numero'].iloc[i-l] for l in [14, 15, 18, 20]}
            return list(cands - rec6)
        return []
    strategies["7. Gatillo Rápido (Solo tras 1 ó 2 fallos)"] = strat_cesta_post_fallo1_2

    # Ejecutar evaluación
    results = []
    
    for name, strat_fn in strategies.items():
        bankroll = 0.0
        peak = 0.0
        max_dd = 0.0
        
        bets_count = 0
        hits_count = 0
        draws_active = 0
        
        gross_profit = 0.0
        gross_loss = 0.0
        
        cur_streak = 0
        loss_streaks = []
        
        # Para test año 1 vs año 2
        pnl_y1 = 0.0
        bets_y1 = 0
        pnl_y2 = 0.0
        bets_y2 = 0
        
        for i in range(start_idx, total):
            actual = df['numero'].iloc[i]
            cands = strat_fn(i, cur_streak)
            
            if not cands:
                # Si no juega, actualizamos racha virtual?
                # La racha la medimos sobre la cesta base para mantener la sincronización
                # O sobre los sorteos jugados
                continue
                
            draws_active += 1
            cost = len(cands)
            bets_count += cost
            
            is_y1 = (i < mid_idx)
            if is_y1:
                bets_y1 += cost
            else:
                bets_y2 += cost
                
            if actual in cands:
                hits_count += 1
                gain = (payout - cost)
                bankroll += gain
                gross_profit += (payout - 1)
                gross_loss += (cost - 1)
                loss_streaks.append(cur_streak)
                cur_streak = 0
                if is_y1:
                    pnl_y1 += gain
                else:
                    pnl_y2 += gain
            else:
                bankroll -= cost
                gross_loss += cost
                cur_streak += 1
                if is_y1:
                    pnl_y1 -= cost
                else:
                    pnl_y2 -= cost
                    
            if bankroll > peak:
                peak = bankroll
            dd = peak - bankroll
            if dd > max_dd:
                max_dd = dd

        max_loss_streak = max(loss_streaks) if loss_streaks else 0
        avg_loss_streak = np.mean(loss_streaks) if loss_streaks else 0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0
        roi = (bankroll / bets_count * 100) if bets_count > 0 else 0
        win_rate = (hits_count / draws_active * 100) if draws_active > 0 else 0
        roi_y1 = (pnl_y1 / bets_y1 * 100) if bets_y1 > 0 else 0
        roi_y2 = (pnl_y2 / bets_y2 * 100) if bets_y2 > 0 else 0
        
        results.append({
            'Nombre': name,
            'Sorteos': draws_active,
            'Fichas': bets_count,
            'Aciertos': hits_count,
            'Win Rate': win_rate,
            'PnL (Bs)': bankroll,
            'ROI (%)': roi,
            'ROI Año 1': roi_y1,
            'ROI Año 2': roi_y2,
            'Max DD (Bs)': max_dd,
            'Profit Factor': profit_factor,
            'Max Sequía': max_loss_streak
        })

    df_res = pd.DataFrame(results)
    
    print("=" * 125)
    print(" COMPARATIVA DE ESTRATEGIAS: BÚSQUEDA DE LA MÁS PRODUCTIVA Y EFICIENTE")
    print("=" * 125)
    
    # Sort by PnL
    df_sorted = df_res.sort_values(by='PnL (Bs)', ascending=False).reset_index(drop=True)
    
    print(f"{'Estrategia':<42} | {'Aciertos':<9} | {'WinRate':<8} | {'PnL (Bs)':<10} | {'ROI (%)':<8} | {'ROI Y1/Y2':<15} | {'Max DD':<8} | {'PF':<5}")
    print("-" * 125)
    for _, r in df_sorted.iterrows():
        roi_str = f"{r['ROI Año 1']:+.1f}%/{r['ROI Año 2']:+.1f}%"
        print(f"{r['Nombre']:<42} | {r['Aciertos']:<9} | {r['Win Rate']:>6.2f}% | {r['PnL (Bs)']:>+10.0f} | {r['ROI (%)']:>+6.2f}% | {roi_str:<15} | {r['Max DD (Bs)']:>7.0f} | {r['Profit Factor']:>4.2f}")
    print("=" * 125)

if __name__ == "__main__":
    find_best_strategy()
