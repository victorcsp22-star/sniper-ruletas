import numpy as np
import pandas as pd

def rigorous_out_of_sample_validation():
    csv_path = r"C:\Users\victo\.gemini\antigravity\scratch\lotto_activo_bot\lotto_activo_2anios.csv"
    df = pd.read_csv(csv_path, encoding='utf-8-sig', dtype={'numero': str})
    df['sort_key'] = pd.to_datetime(df['fecha'] + ' ' + df['hora'], format='%Y-%m-%d %I:%M %p', errors='coerce')
    df = df.sort_values(by='sort_key').reset_index(drop=True)
    
    total = len(df)
    payout = 30.0
    
    # Split chronologically in two halves: Year 1 vs Year 2
    # Midpoint split
    mid_idx = total // 2
    
    df_y1 = df.iloc[:mid_idx].copy()
    df_y2 = df.iloc[mid_idx:].copy()
    
    print("================================================================================")
    print(" VALIDACIÓN RIGUROSA OUT-OF-SAMPLE (AÑO 1 vs AÑO 2)")
    print("================================================================================")
    print(f"Año 1 (In-sample):     {df_y1['fecha'].min()} a {df_y1['fecha'].max()} ({len(df_y1):,} sorteos)")
    print(f"Año 2 (Out-of-sample): {df_y2['fecha'].min()} a {df_y2['fecha'].max()} ({len(df_y2):,} sorteos)")
    print("-" * 80)
    
    for name, df_sub in [("AÑO 1 (Primer año)", df_y1), ("AÑO 2 (Segundo año - Ciego)", df_y2)]:
        # Evaluate Lag 20 not in recent 6
        bets_20, hits_20 = 0, 0
        bets_18, hits_18 = 0, 0
        
        for i in range(25, len(df_sub)):
            actual = df_sub['numero'].iloc[i]
            recent_6 = set(df_sub['numero'].iloc[i-6:i])
            
            # Lag 20
            cand_20 = df_sub['numero'].iloc[i-20]
            if cand_20 not in recent_6:
                bets_20 += 1
                if actual == cand_20:
                    hits_20 += 1
                    
            # Lag 18
            cand_18 = df_sub['numero'].iloc[i-18]
            if cand_18 not in recent_6:
                bets_18 += 1
                if actual == cand_18:
                    hits_18 += 1
                    
        wr_20 = (hits_20 / bets_20) * 100 if bets_20 > 0 else 0
        pnl_20 = hits_20 * payout - bets_20
        roi_20 = (pnl_20 / bets_20) * 100 if bets_20 > 0 else 0

        wr_18 = (hits_18 / bets_18) * 100 if bets_18 > 0 else 0
        pnl_18 = hits_18 * payout - bets_18
        roi_18 = (pnl_18 / bets_18) * 100 if bets_18 > 0 else 0

        print(f"[{name}]")
        print(f"  • Lag 20 (filtrado): Bets={bets_20:,} | Hits={hits_20} | WinRate={wr_20:.2f}% | PnL={pnl_20:+.0f} Bs | ROI={roi_20:+.2f}%")
        print(f"  • Lag 18 (filtrado): Bets={bets_18:,} | Hits={hits_18} | WinRate={wr_18:.2f}% | PnL={pnl_18:+.0f} Bs | ROI={roi_18:+.2f}%")
        print()

if __name__ == "__main__":
    rigorous_out_of_sample_validation()
