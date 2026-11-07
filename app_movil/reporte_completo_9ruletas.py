import os, pandas as pd

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

print("=== REPORTE CONSOLIDADO DE SORTEOS DE HOY (2026-11-02) ===")
for nombre, ruta in rutas.items():
    if not os.path.exists(ruta):
        print(f"[{nombre}] ARCHIVO NO ENCONTRADO: {ruta}")
        continue
    df = pd.read_csv(ruta)
    df['fecha_str'] = df['fecha'].astype(str)
    hoy = df[df['fecha_str'].str.contains('2026-11-02')]
    sorteos = [f"{r['hora']}: #{r['numero']} {r['animal']}" for _, r in hoy.iterrows()]
    print(f"\n{nombre} ({len(sorteos)} sorteos salidos hoy):")
    if sorteos:
        print("  " + " | ".join(sorteos))
    else:
        print("  (Sin sorteos registrados hoy)")
