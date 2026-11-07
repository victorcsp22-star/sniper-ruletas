import os
import sys
import pandas as pd
import numpy as np

sys.path.append(r"C:\Users\victo\nuevas_ruletas")
from config import RULETAS_CONFIG

print("Verificando archivos de las 8 ruletas activas:")
total_draws = 0
for r_name, cfg in RULETAS_CONFIG.items():
    if not cfg.get("active", False):
        continue
    fpath = cfg["file"]
    if os.path.exists(fpath):
        df = pd.read_csv(fpath, dtype={"numero": str})
        df["dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        df = df.dropna(subset=["dt"]).sort_values("dt").reset_index(drop=True)
        total_draws += len(df)
        print(f"  {r_name:28} | Sorteos: {len(df):6} | Desde: {df['dt'].min()} | Hasta: {df['dt'].max()}")
    else:
        print(f"  {r_name:28} | NO EXISTE: {fpath}")

print(f"Total sorteos combinados en las 8 ruletas: {total_draws:,}")
