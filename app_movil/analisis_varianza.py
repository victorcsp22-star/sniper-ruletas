import os, pandas as pd

rutas = {
    "Guacharo Activo": (r"C:\Users\victo\nuevas_ruletas\data_vz\guacharo_activo_2anios.csv", 75),
    "Lotto Activo": (r"C:\Users\victo\nuevas_ruletas\data_vz\lotto_activo_2anios.csv", 38),
    "Ruleta Royal": (r"C:\Users\victo\nuevas_ruletas\data_vz\ruleta_royal_2anios.csv", 38),
    "Lotto Gato": (r"C:\Users\victo\nuevas_ruletas\lotto_gato.csv", 60),
    "Loto Chaima": (r"C:\Users\victo\nuevas_ruletas\loto_chaima.csv", 60),
    "Mega Animal 40": (r"C:\Users\victo\nuevas_ruletas\mega_animal_40.csv", 40),
    "Gatazo": (r"C:\Users\victo\nuevas_ruletas\gatazo.csv", 100),
    "Monje Millonario": (r"C:\Users\victo\nuevas_ruletas\monje_millonario.csv", 60),
    "Granjazo": (r"C:\Users\victo\nuevas_ruletas\granja_millonaria_granjazo.csv", 75),
}

for k, (v, tot) in rutas.items():
    df = pd.read_csv(v)
    hoy = df[df['fecha'] == '2026-11-02']
    nums = [str(n) for n in hoy['numero']]
    print(f"{k} (tamano {tot}, {len(nums)} sorteos): salieron {len(set(nums))} distintos, repeticiones: {len(nums) - len(set(nums))}")
