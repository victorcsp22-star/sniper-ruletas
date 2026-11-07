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

print("=== BALANCE FORMAL DE DISPAROS TEORICOS VS REALES HOY (2026-11-02) ===")
total_disparos = 0
total_hits = 0

for r_name, (fpath, lags, target_stk, use_anti, payout) in rutas.items():
    df = pd.read_csv(fpath)
    df['num_str'] = df['numero'].astype(str).str.strip().str.lstrip("0").replace("", "0")
    df['fecha_str'] = df['fecha'].astype(str)
    
    idx_hoy = df[df['fecha_str'] == '2026-11-02'].index.tolist()
    if not idx_hoy: continue
    start_idx = idx_hoy[0]
    
    streak = 0
    cur_d = None
    seen_today = set()
    prev_was_repeat = False
    
    for i in range(max(lags) + 7, start_idx):
        d = df.loc[i, 'fecha_str']
        act = df.loc[i, 'num_str']
        if d != cur_d:
            cur_d = d
            seen_today = set()
            prev_was_repeat = False
        rec = set(df.loc[i-6:i-1, 'num_str'])
        raw = [df.loc[i-l, 'num_str'] for l in lags]
        c_lag = sorted(list(set(raw) - rec))
        skip_anti = bool(use_anti and prev_was_repeat)
        if c_lag:
            hit = (act in c_lag)
            streak = 0 if hit else streak + 1
        is_rep = (act in seen_today)
        seen_today.add(act)
        prev_was_repeat = is_rep
        
    print(f"\n[{r_name}] Racha al inicio del dia: {streak}")
    for i in idx_hoy:
        act = df.loc[i, 'num_str']
        hora = df.loc[i, 'hora'] if 'hora' in df.columns else ""
        anim = df.loc[i, 'animal'] if 'animal' in df.columns else ""
        rec = set(df.loc[i-6:i-1, 'num_str'])
        raw = [df.loc[i-l, 'num_str'] for l in lags]
        c_lag = sorted(list(set(raw) - rec))
        
        skip_anti = bool(use_anti and prev_was_repeat)
        debio_apostar = (streak in target_stk) and (not skip_anti)
        hit = (act in c_lag)
        
        if debio_apostar:
            total_disparos += 1
            if hit: total_hits += 1
            print(f"  [DISPARO {hora}]: Racha={streak} | Cands={c_lag} | Salio=#{act} {anim} | Hit={hit}")
        else:
            if hit:
                print(f"  (Acierto fuera de racha [{hora}]: Racha={streak} | Cands={c_lag} | Salio=#{act} {anim})")
                
        if c_lag:
            streak = 0 if hit else streak + 1
        is_rep = (act in seen_today)
        seen_today.add(act)
        prev_was_repeat = is_rep

print(f"\n=======================================================")
print(f"RESUMEN REZAGADOS HOY: Total Disparos={total_disparos} | Aciertos={total_hits}")
