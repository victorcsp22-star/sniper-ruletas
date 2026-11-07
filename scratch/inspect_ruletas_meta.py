import os
import glob
import pandas as pd
import numpy as np

VZ_DIR = r"C:\Users\victo\nuevas_ruletas\data_vz"
ROOT_DIR = r"C:\Users\victo\nuevas_ruletas"

files = {
    # 7 Core
    "Lotto Activo": os.path.join(VZ_DIR, "lotto_activo_2anios.csv"),
    "La Granjita": os.path.join(VZ_DIR, "la_granjita_2anios.csv"),
    "Ruleta Royal": os.path.join(VZ_DIR, "ruleta_royal_2anios.csv"),
    "Guacharo Activo": os.path.join(VZ_DIR, "guacharo_activo_2anios.csv"),
    "Gatazo": os.path.join(ROOT_DIR, "gatazo.csv"),
    "Mega Animal 40": os.path.join(ROOT_DIR, "mega_animal_40.csv"),
    "Monje Millonario": os.path.join(ROOT_DIR, "monje_millonario.csv"),
    # Additional / Extended
    "Lotto Activo RD (Lotoven)": os.path.join(ROOT_DIR, "lotto_activo_rd_lotoven_completo.csv"),
    "Lotto Activo RD (2anios)": os.path.join(VZ_DIR, "lotto_activo_rd_2anios.csv"),
    "Lotto Gato": os.path.join(ROOT_DIR, "lotto_gato.csv"),
    "Loto Chaima": os.path.join(ROOT_DIR, "loto_chaima.csv"),
    "Selva Plus": os.path.join(VZ_DIR, "selva_plus_2anios.csv"),
    "Guacharito Millonario": os.path.join(VZ_DIR, "guacharito_millonario_2anios.csv"),
    "Lotto Brasil": os.path.join(VZ_DIR, "lottobrasil_2anios.csv"),
    "Lotto Bicho": os.path.join(VZ_DIR, "lottobicho_2anios.csv")
}

print(f"{'Ruleta':<26} | {'Filas':<6} | {'Fechas':<6} | {'Sorteos/Dia':<11} | {'Unicos':<6} | {'Rango Fechas':<23}")
print("-" * 95)

for name, path in files.items():
    if not os.path.exists(path):
        print(f"{name:<26} | NO EXISTE")
        continue
    df = pd.read_csv(path, dtype={'numero': str})
    # normalize columns
    df.columns = [c.lower().strip() for c in df.columns]
    
    # date handling
    if 'fecha' in df.columns:
        dates = df['fecha'].dropna().unique()
        n_dates = len(dates)
        date_min = str(df['fecha'].iloc[0])
        date_max = str(df['fecha'].iloc[-1])
        draws_per_day = len(df) / n_dates if n_dates > 0 else 0
    else:
        n_dates = 0
        date_min, date_max = "N/A", "N/A"
        draws_per_day = 0
        
    nums = df['numero'].dropna().astype(str).str.strip().unique()
    n_unique = len(nums)
    
    print(f"{name:<26} | {len(df):<6} | {n_dates:<6} | {draws_per_day:<11.1f} | {n_unique:<6} | {date_min} .. {date_max}")
