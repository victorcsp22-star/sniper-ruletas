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
    "Granja Millonaria - Granjazo": (r"C:\Users\victo\nuevas_ruletas\granja_millonaria_granjazo.csv", 75),
}

print("="*80)
print("TODOS LOS RESULTADOS DEL DIA DE HOY (LUNES 2 DE NOVIEMBRE 2026) EN LA PC")
print("="*80)

total_sorteos_hoy = 0
for r_name, (fpath, total_terminales) in rutas.items():
    if not os.path.exists(fpath):
        continue
    df = pd.read_csv(fpath)
    df['fecha_str'] = df['fecha'].astype(str)
    hoy = df[df['fecha_str'] == '2026-11-02']
    total_sorteos_hoy += len(hoy)
    print(f"\n[*] {r_name.upper()} ({len(hoy)} sorteos realizados):")
    for idx, r in hoy.iterrows():
        hora = str(r.get('hora', '')).strip()
        num = str(r.get('numero', '')).strip()
        anim = str(r.get('animal', '')).strip()
        print(f"   - {hora:<9} -> #{num} {anim}")

print("\n" + "="*80)
print(f"TOTAL SORTEOS PROCESADOS HOY EN LA CARTERA: {total_sorteos_hoy} SORTEOS")
print("="*80)
