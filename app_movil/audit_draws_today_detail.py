import pandas as pd

rutas = {
    "Guacharo Activo": (r"C:\Users\victo\nuevas_ruletas\data_vz\guacharo_activo_2anios.csv", [31, 54, 41], [1, 3], False, 60.0),
    "Lotto Activo": (r"C:\Users\victo\nuevas_ruletas\data_vz\lotto_activo_2anios.csv", [20, 18, 15], [1, 2], True, 30.0),
    "Ruleta Royal": (r"C:\Users\victo\nuevas_ruletas\data_vz\ruleta_royal_2anios.csv", [19, 16, 31], [1], True, 30.0),
    "Lotto Gato": (r"C:\Users\victo\nuevas_ruletas\lotto_gato.csv", [18, 38, 14], [1, 2], False, 60.0),
    "Loto Chaima": (r"C:\Users\victo\nuevas_ruletas\loto_chaima.csv", [49, 41, 35], [0, 1], False, 60.0),
    "Mega Animal 40": (r"C:\Users\victo\nuevas_ruletas\mega_animal_40.csv", [36, 17, 39], [1, 2], False, 30.0),
    "Gatazo": (r"C:\Users\victo\nuevas_ruletas\gatazo.csv", [35, 41, 15], [1], False, 60.0),
    "Monje Millonario": (r"C:\Users\victo\nuevas_ruletas\monje_millonario.csv", [45, 14, 38], [1], False, 60.0),
    "Granjazo": (r"C:\Users\victo\nuevas_ruletas\granja_millonaria_granjazo.csv", [46, 50, 24], [1], False, 60.0),
}

print("=== VERIFICACION DE CANDIDATOS EXACTOS EN LOS SORTEOS DE HOY (2026-11-02) ===")
for r_name, (fpath, lags, target_stk, use_anti, payout) in rutas.items():
    df = pd.read_csv(fpath)
    df['num_str'] = df['numero'].astype(str).str.strip().str.lstrip("0").replace("", "0")
    df['fecha_str'] = df['fecha'].astype(str)
    
    # Tomar índices de hoy
    idx_hoy = df[df['fecha_str'] == '2026-11-02'].index.tolist()
    if not idx_hoy:
        continue
        
    print(f"\n================ {r_name} (Sorteos hoy: {len(idx_hoy)}) ================")
    # Para cada sorteo de hoy, calcular exactamente los candidatos teóricos y si acertó
    for i in idx_hoy:
        hora = df.loc[i, 'hora'] if 'hora' in df.columns else ""
        salio = df.loc[i, 'num_str']
        animal = df.loc[i, 'animal'] if 'animal' in df.columns else ""
        
        # Historial hasta i-1
        hist_nums = df.loc[:i-1, 'num_str'].tolist()
        rec_set = set(hist_nums[-6:])
        raw_cands = [hist_nums[-l] for l in lags if len(hist_nums) >= l]
        cands_lag = sorted(list(set(raw_cands) - rec_set))
        
        # Calcular racha histórica en i
        # ...
        hit_lag = (salio in cands_lag)
        salio_en_raw = (salio in raw_cands)
        salio_en_rec = (salio in rec_set)
        
        print(f"[{hora}] Salió #{salio} {animal} | Cands Lag: {cands_lag} (Hit: {hit_lag}) | Raw: {raw_cands} | En rec: {salio_en_rec}")
