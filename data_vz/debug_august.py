import pandas as pd

def debug_august_2025():
    configs = {
        "Lotto Activo": {"file": "lotto_activo_2anios.csv", "lags": [14, 15, 18, 20]},
        "La Granjita": {"file": "la_granjita_2anios.csv", "lags": [14, 15, 17]},
        "Ruleta Royal": {"file": "ruleta_royal_2anios.csv", "lags": [16, 19, 21, 23]},
        "Guacharo Activo": {"file": "guacharo_activo_2anios.csv", "lags": [25, 31, 41, 42]}
    }
    
    # Check each lottery during August 2025: how many wins did they have?
    print("=== ACIERTOS POR RULETA EN AGOSTO 2025 (TODO EL MES) ===")
    for lotto, cfg in configs.items():
        df = pd.read_csv(cfg["file"], encoding="utf-8-sig", dtype={"numero": str})
        df["dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        df = df.dropna(subset=["dt"]).sort_values(by="dt").reset_index(drop=True)
        
        nums = df["numero"].tolist()
        lags = cfg["lags"]
        max_l = max(lags)
        
        august_hits = []
        streak = 0
        for i in range(max_l + 6, len(nums)):
            actual = nums[i]
            rec6 = set(nums[i-6:i])
            cands = list({nums[i-l] for l in lags} - rec6)
            hit = (actual in cands)
            cost = len(cands)
            date_str = df["fecha"].iloc[i]
            
            if streak == 1 and cost > 0:
                if "2025-08" in date_str:
                    august_hits.append((date_str, df["hora"].iloc[i], lotto, hit, actual, cands))
                    
            if cost > 0:
                if hit:
                    streak = 0
                else:
                    streak += 1
                    
        hits_in_aug = [x for x in august_hits if x[3]]
        print(f"{lotto}: {len(august_hits)} apuestas en agosto, {len(hits_in_aug)} aciertos.")
        for h in hits_in_aug:
            print(f"   -> Ganó: {h[0]} {h[1]} | Salió {h[4]} en candidatos {h[5]}")

if __name__ == "__main__":
    debug_august_2025()
