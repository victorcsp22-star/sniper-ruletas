import os, glob, pandas as pd

# Mapeo de las ruletas pedidas por el usuario
solicitadas = {
    "Guacharo Activo": [r"C:\Users\victo\nuevas_ruletas\data_vz\guacharo_activo_2anios.csv"],
    "Ruleta Royal": [r"C:\Users\victo\nuevas_ruletas\data_vz\ruleta_royal_2anios.csv"],
    "El Guacharito Millonario": [r"C:\Users\victo\nuevas_ruletas\data_vz\guacharito_millonario_2anios.csv"],
    "Lotto Activo": [r"C:\Users\victo\nuevas_ruletas\data_vz\lotto_activo_2anios.csv"],
    "Lotto Activo RD Internacional": [r"C:\Users\victo\nuevas_ruletas\lotto_activo_rd_lotoven_completo.csv", r"C:\Users\victo\nuevas_ruletas\lotto_activo_rd_internacional.csv", r"C:\Users\victo\nuevas_ruletas\data_vz\lotto_activo_rd_2anios.csv"],
    "Selva Plus": [r"C:\Users\victo\nuevas_ruletas\data_vz\selva_plus_2anios.csv"],
    "Granja Millonaria - Granjazo": [r"C:\Users\victo\nuevas_ruletas\granja_millonaria_granjazo.csv"],
    "La Granjita": [r"C:\Users\victo\nuevas_ruletas\data_vz\la_granjita_2anios.csv"],
    "Monje Millonario": [r"C:\Users\victo\nuevas_ruletas\monje_millonario.csv"],
    "Loto Chaima": [r"C:\Users\victo\nuevas_ruletas\loto_chaima.csv"],
    "Granja Millonaria - Animalitos": [r"C:\Users\victo\nuevas_ruletas\granja_millonaria_animalitos.csv"],
    "Gatazo": [r"C:\Users\victo\nuevas_ruletas\gatazo.csv"],
    "Mega Animal 40": [r"C:\Users\victo\nuevas_ruletas\mega_animal_40.csv"],
    "Tropi Gana": [r"C:\Users\victo\nuevas_ruletas\tropi_gana.csv"],
    "Lotto Gato": [r"C:\Users\victo\nuevas_ruletas\lotto_gato.csv"]
}

print(f"{'RULETA':<32} | {'EXISTE':<8} | {'FILAS':<8} | {'FECHA MIN':<12} | {'FECHA MAX':<12} | {'ARCHIVO'}")
print("-" * 115)

for nombre, paths in solicitadas.items():
    found = None
    for p in paths:
        if os.path.exists(p) and os.path.getsize(p) > 100:
            found = p
            break
    
    if found:
        try:
            df = pd.read_csv(found)
            fechas = df['fecha'].dropna().astype(str).tolist()
            f_min = min(fechas) if fechas else 'N/A'
            f_max = max(fechas) if fechas else 'N/A'
            print(f"{nombre:<32} | {'SI':<8} | {len(df):<8} | {f_min:<12} | {f_max:<12} | {os.path.basename(found)}")
        except Exception as e:
            print(f"{nombre:<32} | {'ERROR':<8} | {0:<8} | {'N/A':<12} | {'N/A':<12} | {e}")
    else:
        print(f"{nombre:<32} | {'NO':<8} | {0:<8} | {'N/A':<12} | {'N/A':<12} | Falta descargar")
