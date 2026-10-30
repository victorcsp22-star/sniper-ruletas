import numpy as np
import pandas as pd

def test_virtual_streak_triggers():
    csv_path = r"C:\Users\victo\.gemini\antigravity\scratch\lotto_activo_bot\lotto_activo_2anios.csv"
    df = pd.read_csv(csv_path, encoding='utf-8-sig', dtype={'numero': str})
    df['sort_key'] = pd.to_datetime(df['fecha'] + ' ' + df['hora'], format='%Y-%m-%d %I:%M %p', errors='coerce')
    df = df.sort_values(by='sort_key').reset_index(drop=True)
    
    total = len(df)
    payout = 30.0
    start_idx = 25
    mid_idx = total // 2

    # Evaluaremos gatillos basados en la racha VIRTUAL de la Cesta 4 y del Dúo Armónico
    # Es decir: el sistema monitorea en papel cada sorteo.
    # Cuando ocurre la condición X (ej: tras fallar 1 sorteo), se activa la apuesta real.
    
    # Probemos con el DÚO ARMÓNICO (Lags 18 y 20) y la CESTA 4
    for model_name, lags in [("DÚO ARMÓNICO (Lags 18 y 20)", [18, 20]), ("CESTA 4 (Lags 14, 15, 18, 20)", [14, 15, 18, 20])]:
        print(f"\n================================================================================")
        print(f" OPTIMIZACIÓN DE GATILLOS: {model_name}")
        print(f"================================================================================")
        
        # 1. Monitoreo continuo y registro de qué sorteos acertaría virtualmente
        virtual_hits = []
        virtual_cands = []
        
        for i in range(start_idx, total):
            actual = df['numero'].iloc[i]
            rec6 = set(df['numero'].iloc[i-6:i])
            cands = list({df['numero'].iloc[i-l] for l in lags} - rec6)
            hit = (actual in cands)
            virtual_hits.append(hit)
            virtual_cands.append(cands)
            
        # Simular diferentes filtros de gatillo:
        triggers = [
            ("A. Siempre Activo (Jugar todos los sorteos válidos)", lambda s: True),
            ("B. Gatillo Post-Fallo 1 (Apostar ÚNICAMENTE tras 1 fallo previo)", lambda s: s == 1),
            ("C. Gatillo Doble Rebote (Apostar tras 1 o tras 2 fallos)", lambda s: s in [1, 2]),
            ("D. Salto de Zona Fría (Jugar siempre, EXCEPTO cuando lleva 3 a 6 fallos)", lambda s: s not in [3, 4, 5, 6]),
            ("E. Francotirador de Sequía (Apostar SOLO tras 9 o más fallos seguidos)", lambda s: s >= 9)
        ]
        
        print(f"{'Gatillo Táctico':<45} | {'Apuestas':<10} | {'Aciertos':<8} | {'WinRate':<8} | {'PnL (Bs)':<10} | {'ROI (%)':<8} | {'Max DD':<7}")
        print("-" * 105)
        
        for t_name, cond_fn in triggers:
            bankroll = 0.0
            peak = 0.0
            max_dd = 0.0
            bets = 0
            hits = 0
            streak = 0
            
            for idx in range(len(virtual_hits)):
                hit = virtual_hits[idx]
                cands = virtual_cands[idx]
                cost = len(cands)
                
                # Evaluar si la condición previa se cumple
                if cond_fn(streak) and cost > 0:
                    bets += cost
                    if hit:
                        hits += 1
                        bankroll += (payout - cost)
                    else:
                        bankroll -= cost
                        
                    if bankroll > peak:
                        peak = bankroll
                    dd = peak - bankroll
                    if dd > max_dd:
                        max_dd = dd
                        
                # Actualizar racha virtual del sistema
                if hit:
                    streak = 0
                else:
                    streak += 1
                    
            roi = (bankroll / bets * 100) if bets > 0 else 0
            wr = (hits / (bets / (len(lags) if len(lags)>0 else 1)) * 100) if bets > 0 else 0
            print(f"{t_name:<45} | {bets:<10} | {hits:<8} | {wr:>6.2f}% | {bankroll:>+10.0f} | {roi:>+6.2f}% | {max_dd:>7.0f}")

if __name__ == "__main__":
    test_virtual_streak_triggers()
