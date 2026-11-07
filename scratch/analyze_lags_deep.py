import os
import pandas as pd
import numpy as np
from scipy import stats

VZ_DIR = r"C:\Users\victo\nuevas_ruletas\data_vz"
ROOT_DIR = r"C:\Users\victo\nuevas_ruletas"

RULETAS = {
    "Lotto Activo": {"file": os.path.join(VZ_DIR, "lotto_activo_2anios.csv"), "payout": 30.0, "current_lags": [20, 18, 14], "rec_w": 6},
    "La Granjita": {"file": os.path.join(VZ_DIR, "la_granjita_2anios.csv"), "payout": 30.0, "current_lags": [15, 17], "rec_w": 8},
    "Ruleta Royal": {"file": os.path.join(VZ_DIR, "ruleta_royal_2anios.csv"), "payout": 30.0, "current_lags": [16, 19, 31], "rec_w": 6},
    "Guacharo Activo": {"file": os.path.join(VZ_DIR, "guacharo_activo_2anios.csv"), "payout": 60.0, "current_lags": [31, 41, 25, 42, 35], "rec_w": 8},
    "Gatazo": {"file": os.path.join(ROOT_DIR, "gatazo.csv"), "payout": 60.0, "current_lags": [35, 22, 20], "rec_w": 6},
    "Mega Animal 40": {"file": os.path.join(ROOT_DIR, "mega_animal_40.csv"), "payout": 30.0, "current_lags": [18, 21, 37], "rec_w": 8},
    "Monje Millonario": {"file": os.path.join(ROOT_DIR, "monje_millonario.csv"), "payout": 60.0, "current_lags": [24, 35, 37], "rec_w": 6},
    "Lotto Activo RD": {"file": os.path.join(ROOT_DIR, "lotto_activo_rd_lotoven_completo.csv"), "payout": 30.0, "current_lags": [21, 39, 50], "rec_w": 6},
    "Lotto Gato": {"file": os.path.join(ROOT_DIR, "lotto_gato.csv"), "payout": 30.0, "current_lags": [19, 38, 16], "rec_w": 6},
    "Loto Chaima": {"file": os.path.join(ROOT_DIR, "loto_chaima.csv"), "payout": 40.0, "current_lags": [35, 29, 38], "rec_w": 6},
    "Selva Plus": {"file": os.path.join(VZ_DIR, "selva_plus_2anios.csv"), "payout": 80.0, "current_lags": [20, 24, 36], "rec_w": 6},
    "Guacharito Millonario": {"file": os.path.join(VZ_DIR, "guacharito_millonario_2anios.csv"), "payout": 80.0, "current_lags": [24, 36, 48], "rec_w": 6}
}

def analyze_individual_lags():
    print("=" * 110)
    print("AUDITORÍA INSTITUCIONAL DE LAGS INDIVIDUALES: CONDICIONAL A PURGA DE RECENCIA")
    print("=" * 110)
    
    for r_name, cfg in RULETAS.items():
        if not os.path.exists(cfg["file"]):
            continue
        df = pd.read_csv(cfg["file"], dtype={'numero': str})
        df['numero'] = df['numero'].astype(str).str.strip()
        
        # Sort chronologically
        if 'fecha' in df.columns and 'hora' in df.columns:
            df['dt'] = pd.to_datetime(df['fecha'] + ' ' + df['hora'], format='%Y-%m-%d %I:%M %p', errors='coerce')
            df = df.dropna(subset=['dt']).sort_values('dt').reset_index(drop=True)
            
        nums = df['numero'].tolist()
        total = len(nums)
        k_uniq = len(set(nums))
        p0 = 1.0 / k_uniq
        rec_w = cfg["rec_w"]
        
        print(f"\n>>> {r_name} (N={total}, K={k_uniq}, p0={p0*100:.2f}%, rec_w={rec_w})")
        print(f"    Lags Actuales: {cfg['current_lags']}")
        
        lag_stats = []
        for l in range(1, 61):
            hits_raw = 0
            trials_raw = 0
            hits_purged = 0
            trials_purged = 0
            
            for i in range(max(l, rec_w), total):
                cand = nums[i - l]
                target = nums[i]
                rec_set = set(nums[i - rec_w:i])
                
                # Raw
                trials_raw += 1
                if cand == target:
                    hits_raw += 1
                    
                # Purged (cand not in recent window)
                if cand not in rec_set:
                    trials_purged += 1
                    if cand == target:
                        hits_purged += 1
                        
            p_raw = hits_raw / trials_raw if trials_raw > 0 else 0
            p_purged = hits_purged / trials_purged if trials_purged > 0 else 0
            se = np.sqrt(p0 * (1 - p0) / trials_purged) if trials_purged > 0 else 1
            z_purged = (p_purged - p0) / se if se > 0 else 0
            edge_pct = (p_purged - p0) / p0 * 100
            
            lag_stats.append({
                'lag': l,
                'p_purged': p_purged,
                'pct_purged': p_purged * 100,
                'z': z_purged,
                'edge_pct': edge_pct,
                'trials_purged': trials_purged,
                'hits_purged': hits_purged,
                'in_current': l in cfg['current_lags']
            })
            
        df_lags = pd.DataFrame(lag_stats)
        
        # Top 10 by Z-score
        top_by_z = df_lags.sort_values(by='z', ascending=False).head(10)
        print("    TOP 10 Lags Purged (Mayor Edge / Z-score):")
        for _, r in top_by_z.iterrows():
            marker = " [ACTUAL]" if r['in_current'] else ""
            print(f"      Lag {int(r['lag']):2d}: WR={r['pct_purged']:.2f}% (Edge vs p0: {r['edge_pct']:+5.1f}%, Z={r['z']:+5.2f}, n={int(r['trials_purged'])}){marker}")
            
        # Check performance of current lags specifically
        print("    Desempeño de Lags Actuales:")
        for l in cfg['current_lags']:
            sub = df_lags[df_lags['lag'] == l]
            if not sub.empty:
                r = sub.iloc[0]
                rank = (df_lags['z'] > r['z']).sum() + 1
                print(f"      Lag {l:2d}: WR={r['pct_purged']:.2f}% (Edge: {r['edge_pct']:+5.1f}%, Z={r['z']:+5.2f}, Rank: #{rank}/60)")

if __name__ == "__main__":
    analyze_individual_lags()
