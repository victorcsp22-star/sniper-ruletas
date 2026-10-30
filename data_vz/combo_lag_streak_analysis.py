import numpy as np
import pandas as pd
from collections import defaultdict

def run_combo_analysis():
    csv_path = r"C:\Users\victo\.gemini\antigravity\scratch\lotto_activo_bot\lotto_activo_2anios.csv"
    df = pd.read_csv(csv_path, encoding='utf-8-sig', dtype={'numero': str})
    df['sort_key'] = pd.to_datetime(df['fecha'] + ' ' + df['hora'], format='%Y-%m-%d %I:%M %p', errors='coerce')
    df = df.sort_values(by='sort_key').reset_index(drop=True)
    
    total = len(df)
    payout = 30.0
    start_idx = 20

    print("=========================================================================================")
    print(" ANÁLISIS DE LA CESTA DE JUEGO: LAGS 14, 15, 18 Y 20 (COMBINADOS E INDIVIDUALES)")
    print("=========================================================================================\n")

    # Modos a analizar:
    # Modo 1: Cesta Completa (Jugar los 4 números simultáneamente en cada sorteo)
    # Modo 2: Cesta Completa con Filtro (excluyendo candidatos que estén en los últimos 6 sorteos)
    # Modo 3: Cada Lag individual (14, 15, 18, 20)
    
    configs = [
        ("Cesta Combinada (Lags 14, 15, 18, 20) - SIN FILTRO", False),
        ("Cesta Combinada (Lags 14, 15, 18, 20) - CON FILTRO (Excluye últimos 6)", True)
    ]
    
    for title, use_filter in configs:
        print("=" * 90)
        print(f" {title.upper()}")
        print("=" * 90)
        
        draws_evaluated = 0
        total_bets_placed = 0
        hits = 0
        pnl = 0.0
        
        # Secuencia de resultados binarios: 1 = acierto en el sorteo, 0 = fallo
        outcomes = []
        candidates_per_draw = []
        
        for i in range(start_idx, total):
            actual = df['numero'].iloc[i]
            recent_6 = set(df['numero'].iloc[i-6:i]) if use_filter else set()
            
            cands = [
                df['numero'].iloc[i-14],
                df['numero'].iloc[i-15],
                df['numero'].iloc[i-18],
                df['numero'].iloc[i-20]
            ]
            
            # Quitar duplicados entre los 4 lags
            unique_cands = set(cands)
            if use_filter:
                unique_cands = {c for c in unique_cands if c not in recent_6}
                
            if len(unique_cands) == 0:
                continue
                
            draws_evaluated += 1
            cost = len(unique_cands)
            total_bets_placed += cost
            candidates_per_draw.append(cost)
            
            if actual in unique_cands:
                hits += 1
                outcomes.append(1)
                pnl += (payout - cost)
            else:
                outcomes.append(0)
                pnl -= cost
                
        avg_cands = np.mean(candidates_per_draw)
        hit_rate_draw = (hits / draws_evaluated) * 100
        roi = (pnl / total_bets_placed) * 100
        
        # Umbral teórico para la cesta:
        # Si juegas M animales que pagan 30x, ganas si aciertas 1 (paga 30).
        # Costo = M. Retorno esperado = M * p * 30 - M.
        # Break-even requiere que p > 1/30 (3.33% por animal).
        # Para la cesta de ~3.8 animales, el hit rate requerido por sorteo es ~3.8 / 30 = 12.67%.
        be_hit_rate = (avg_cands / payout) * 100
        
        print(f"• Sorteos jugados:               {draws_evaluated:,}")
        print(f"• Total de apuestas (fichas):    {total_bets_placed:,} (promedio {avg_cands:.2f} animales por sorteo)")
        print(f"• Total de sorteos con ACIERTO:  {hits:,} de {draws_evaluated:,}")
        print(f"• Tasa de Acierto por Sorteo:    {hit_rate_draw:.2f}% (Umbral Break-Even: {be_hit_rate:.2f}%)")
        print(f"• PnL Neto:                      {pnl:+.0f} Bs")
        print(f"• Retorno de Inversión (ROI):    {roi:+.2f}%\n")
        
        # -------------------------------------------------------------
        # ANÁLISIS CONDICIONAL: LUEGO DE GANAR 1, PERDER 1, 2, 3...
        # -------------------------------------------------------------
        # Queremos saber:
        # Dado que el estado actual es "k pérdidas consecutivas" (o después de ganar),
        # ¿cuántas veces ocurrió ese estado y cuántas veces se ganó en el siguiente sorteo?
        
        state_total = defaultdict(int)
        state_wins = defaultdict(int)
        
        # Streaks distribution
        loss_streaks = []
        cur_loss = 0
        
        for idx in range(len(outcomes)):
            res = outcomes[idx]
            
            # Registrar el estado previo
            state_key = cur_loss
            state_total[state_key] += 1
            if res == 1:
                state_wins[state_key] += 1
                loss_streaks.append(cur_loss)
                cur_loss = 0
            else:
                cur_loss += 1
                
        max_streak_observed = max(loss_streaks) if loss_streaks else 0
        avg_streak = np.mean(loss_streaks) if loss_streaks else 0
        
        print(f"--- SECUENCIA CONDICIONAL DE ACIERTOS Y RACHAS ---")
        print(f"• Racha máxima de pérdidas consecutivas: {max_streak_observed} sorteos")
        print(f"• Racha promedio de pérdidas entre aciertos: {avg_streak:.1f} sorteos\n")
        
        print(f"{'Condición Previa':<32} | {'Ocasiones':<10} | {'Aciertos Sgte':<14} | {'Win Rate Sgte':<14} | {'Desviación vs Promedio'}")
        print("-" * 92)
        
        # Mostrar después de ganar 1 (cur_loss == 0)
        tot_0 = state_total[0]
        win_0 = state_wins[0]
        wr_0 = (win_0 / tot_0) * 100 if tot_0 > 0 else 0
        diff_0 = wr_0 - hit_rate_draw
        print(f"{'Luego de GANAR 1 (Racha = 0)':<32} | {tot_0:<10} | {win_0:<14} | {wr_0:>6.2f}%       | {diff_0:>+6.2f}%")
        
        # Mostrar luego de perder 1, 2, 3... hasta 15
        for k in range(1, 16):
            tot_k = state_total[k]
            win_k = state_wins[k]
            if tot_k > 0:
                wr_k = (win_k / tot_k) * 100
                diff_k = wr_k - hit_rate_draw
                print(f"{f'Luego de PERDER {k} seguido(s)':<32} | {tot_k:<10} | {win_k:<14} | {wr_k:>6.2f}%       | {diff_k:>+6.2f}%")
            else:
                break
                
        # Distribución de rachas de pérdidas
        print("\n• Distribución acumulada de rachas de fallos (¿En cuántos turnos se corta la pérdida?):")
        streak_counts = pd.Series(loss_streaks).value_counts().sort_index()
        cum_pct = 0.0
        tot_streaks = len(loss_streaks)
        for s_len in range(0, min(12, max_streak_observed + 1)):
            cnt = streak_counts.get(s_len, 0)
            pct = (cnt / tot_streaks) * 100
            cum_pct += pct
            label = "Gana de inmediato (Back-to-back)" if s_len == 0 else f"Corta tras {s_len} fallo(s)"
            print(f"   - {label:<35}: {cnt:4d} veces ({pct:5.2f}%) | Acumulado: {cum_pct:5.2f}%")
            
        print("\n")

if __name__ == "__main__":
    run_combo_analysis()
