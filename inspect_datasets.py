import glob
import os
import sys
import pandas as pd

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

files = glob.glob(r"C:\Users\victo\nuevas_ruletas\*.csv")

print("=" * 105)
print(" 📊 RESUMEN DE ESTRUCTURA Y SORTEOS DESCARGADOS")
print("=" * 105)

for f in sorted(files):
    if "resumen" in f:
        continue
    df = pd.read_csv(f, dtype={"numero": str})
    fname = os.path.basename(f)
    nums = df["numero"].dropna().unique()
    hours = df["hora"].dropna().unique()
    min_f = df["fecha"].min()
    max_f = df["fecha"].max()
    
    # Muestra de primeros 3 animales
    sample_animals = []
    for _, r in df.dropna(subset=["numero", "animal"]).head(5).iterrows():
        sample_animals.append(f"{r['numero']}-{r['animal']}")
    
    print(f"File: {fname:<32}")
    print(f"  - Sorteos Totales: {len(df):,}")
    print(f"  - Números Únicos:  {len(nums)} (Ejemplos: {', '.join(sample_animals[:3])})")
    print(f"  - Horas por día:   {len(hours)} ({', '.join(list(hours)[:4])}...)")
    print(f"  - Rango Temporal:  {min_f} a {max_f}")
    print("-" * 105)
