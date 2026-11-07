import os
import sys
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = r"C:\Users\victo\nuevas_ruletas"
df = pd.read_csv(os.path.join(ROOT_DIR, "data_vz", "ruleta_royal_2anios.csv"))
df["numero"] = df["numero"].astype(str).str.strip()
df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
df = df.dropna(subset=["sort_dt"]).sort_values("sort_dt").reset_index(drop=True)

# Trace for Oct 27:
oct27_df = df[df["fecha"] == "2026-10-27"].copy()
lags = [16, 19, 31]

print("--- EVALUANDO SORTEOS DEL 27-OCTUBRE EN RULETA ROYAL ---")
for idx in oct27_df.index:
    row = df.iloc[idx]
    actual = row["numero"]
    h = row["hora"]
    
    # Base rec_w=6, no anti-cluster
    nums = df["numero"].tolist()
    rec6 = set(nums[idx-6:idx])
    raw = [nums[idx-l] for l in lags]
    cands_b = sorted(list(set(raw) - rec6))
    hit_b = actual in cands_b
    
    # Max rec_w=6, anti-cluster True
    day_draws = df[(df["fecha"] == "2026-10-27") & (df.index < idx)]["numero"].tolist()
    is_ac = len(day_draws) >= 2 and day_draws[-1] in day_draws[:-1]
    
    print(f"Hora {h:>8} | Salido: {actual:>2} ({row['animal']}) | Cands: {cands_b} | Hit: {hit_b} | AntiClusterBlocked: {is_ac}")
