import glob, os, pandas as pd

rutas = {
    "Guacharo Activo": r"C:\Users\victo\nuevas_ruletas\data_vz\guacharo_activo_2anios.csv",
    "Lotto Activo": r"C:\Users\victo\nuevas_ruletas\data_vz\lotto_activo_2anios.csv",
    "Ruleta Royal": r"C:\Users\victo\nuevas_ruletas\data_vz\ruleta_royal_2anios.csv",
    "Lotto Gato": r"C:\Users\victo\nuevas_ruletas\lotto_gato.csv",
    "Loto Chaima": r"C:\Users\victo\nuevas_ruletas\loto_chaima.csv",
    "Mega Animal 40": r"C:\Users\victo\nuevas_ruletas\mega_animal_40.csv",
    "Gatazo": r"C:\Users\victo\nuevas_ruletas\gatazo.csv",
    "Monje Millonario": r"C:\Users\victo\nuevas_ruletas\monje_millonario.csv",
    "Granjazo": r"C:\Users\victo\nuevas_ruletas\granja_millonaria_granjazo.csv",
}

print("=== DISTRIBUCION DE SORTEOS HOY ===")
total_sorteos_hoy = 0
for k, v in rutas.items():
    if os.path.exists(v):
        df = pd.read_csv(v)
        c = len(df[df['fecha'] == '2026-11-02'])
        total_sorteos_hoy += c
        print(f"- {k}: {c} sorteos")
print(f"\nTOTAL SORTEOS TRANSCURRIDOS HOY EN LAS 9 RULETAS: {total_sorteos_hoy}")
