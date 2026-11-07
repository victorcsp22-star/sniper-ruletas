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
    "Granja Millonaria - Granjazo": (r"C:\Users\victo\nuevas_ruletas\granja_millonaria_granjazo.csv", [46, 50, 24], [1], False, 60.0),
}

# Animales
animales_map = {}
for r_name, (fpath, *rest) in rutas.items():
    df = pd.read_csv(fpath)
    for idx, r in df.iterrows():
        n = str(r['numero']).strip().lstrip("0") or "0"
        a = str(r['animal']).strip()
        animales_map[(r_name, n)] = a

disparos_puros = []

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
            cost = len(c_lag)
            win_val = payout if hit else 0.0
            cands_named = [f"#{c} {animales_map.get((r_name, c), '')}" for c in c_lag]
            disparos_puros.append({
                "hora": hora,
                "ruleta": r_name,
                "racha": streak,
                "cands": ", ".join(cands_named),
                "fichas": cost,
                "salio": f"#{act} {anim}",
                "hit": hit,
                "payout": payout,
                "pnl_u": win_val - cost,
                "pnl_bs": (win_val - cost) * 100.0
            })
            
        if c_lag:
            streak = 0 if hit else streak + 1
        is_rep = (act in seen_today)
        seen_today.add(act)
        prev_was_repeat = is_rep

import datetime
def parse_time(h_str):
    try:
        return datetime.datetime.strptime(str(h_str).strip(), "%I:%M %p").time()
    except Exception:
        return datetime.time(0, 0)

disparos_puros.sort(key=lambda x: parse_time(x['hora']))

print("================================================================================")
print("DISPAROS OFICIALES DEL BOT DE LA PC (ESTRATEGIA PURA DE REZAGADOS)")
print("LUNES 2 DE NOVIEMBRE DE 2026")
print("================================================================================")

tot_fichas = 0
tot_pnl_bs = 0
hits_count = 0

for idx, d in enumerate(disparos_puros, 1):
    res_str = "GANADA (+)" if d['hit'] else "PERDIDA (-)"
    tot_fichas += d['fichas']
    tot_pnl_bs += d['pnl_bs']
    if d['hit']: hits_count += 1
    print(f"\n{idx:02d}. [{d['hora']}] {d['ruleta']} (Pago {d['payout']:.0f}x)")
    print(f"    • Racha Objetivo: {d['racha']}")
    print(f"    • Candidatos ({d['fichas']} fichas): {d['cands']}")
    print(f"    • Resultado: Salió {d['salio']} -> {res_str}")
    print(f"    • PnL: {d['pnl_u']:+,.1f} U (Bs {d['pnl_bs']:+,.2f})")

print("\n" + "="*80)
print("RESUMEN GENERAL DEL DÍA (ESTRATEGIA OFICIAL):")
print("="*80)
print(f"• Total Disparos Efectuados: {len(disparos_puros)}")
print(f"• Aciertos (Hits): {hits_count}")
print(f"• Fallos: {len(disparos_puros) - hits_count}")
print(f"• Fichas Invertidas: {tot_fichas} fichas (@ Bs 100.00 = Bs {tot_fichas * 100:,.2f})")
print(f"• PnL Neto del Día: Bs {tot_pnl_bs:+,.2f}")
print("================================================================================")
