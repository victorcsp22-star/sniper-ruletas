import os
import sys
import pandas as pd

sys.path.append(r"C:\Users\victo\nuevas_ruletas")
from config import RULETAS_CONFIG

print("=" * 80)
print("AUDITORÍA DE SORTEOS DE HOY (2026-11-05) POR RULETA:")
print("=" * 80)

for r_name, cfg in RULETAS_CONFIG.items():
    if not cfg.get("active", False):
        continue
    fpath = cfg["file"]
    if not os.path.exists(fpath):
        continue
    df = pd.read_csv(fpath, dtype={"numero": str})
    df_today = df[df["fecha"] == "2026-11-05"].sort_values("hora")
    print(f"\n>>> {r_name} (Sorteos hoy: {len(df_today)}) <<<")
    if df_today.empty:
        print("   (Sin sorteos registrados hoy)")
    for _, row in df_today.iterrows():
        print(f"   [{row.get('hora')}] #{row.get('numero')} {row.get('animal')}")
