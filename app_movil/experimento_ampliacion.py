import os, sys, datetime
import pandas as pd
import numpy as np

ROOT_DIR = r"C:\Users\victo\nuevas_ruletas"

# Ruletas y sus tamaños
RULETAS_DATA = {
    "Lotto Gato": (os.path.join(ROOT_DIR, "lotto_gato.csv"), [18, 38, 14], [1, 2], 6, False, [], 60.0, 60),
    "Loto Chaima": (os.path.join(ROOT_DIR, "loto_chaima.csv"), [49, 41, 35], [0, 1], 6, False, [], 60.0, 60),
    "Guacharo Activo": (os.path.join(ROOT_DIR, "data_vz", "guacharo_activo_2anios.csv"), [31, 54, 41], [1, 3], 8, False, ["75"], 60.0, 75),
    "Lotto Activo": (os.path.join(ROOT_DIR, "data_vz", "lotto_activo_2anios.csv"), [20, 18, 15], [1, 2], 6, True, [], 30.0, 38),
    "Ruleta Royal": (os.path.join(ROOT_DIR, "data_vz", "ruleta_royal_2anios.csv"), [19, 16, 31], [1], 6, True, [], 30.0, 38),
    "Mega Animal 40": (os.path.join(ROOT_DIR, "mega_animal_40.csv"), [18, 20, 43], [1, 2, 3], 8, False, ["4"], 30.0, 40),
    "Gatazo": (os.path.join(ROOT_DIR, "gatazo.csv"), [35, 9, 20], [1], 6, False, ["11"], 60.0, 100),
    "Monje Millonario": (os.path.join(ROOT_DIR, "monje_millonario.csv"), [24, 42, 48], [0, 1], 6, False, ["75"], 60.0, 60),
    "Granja Millonaria - Granjazo": (os.path.join(ROOT_DIR, "granja_millonaria_granjazo.csv"), [45, 26, 15], [1, 3], 6, False, [], 60.0, 75)
}

# Cargar y preparar datos una sola vez
preloaded_data = {}
for r_name, (fpath, lags, target_stk, rec_w, use_anti, bl, payout, tot_terms) in RULETAS_DATA.items():
    if not os.path.exists(fpath): continue
    df = pd.read_csv(fpath)
    if len(df) < 50: continue
    df['num_str'] = df['numero'].astype(str).str.strip().str.lstrip("0").replace("", "0")
    df['fecha_str'] = df['fecha'].astype(str)
    preloaded_data[r_name] = {
        "nums": df['num_str'].tolist(),
        "dates": df['fecha_str'].tolist(),
        "horas": df['hora'].astype(str).tolist() if 'hora' in df.columns else [""] * len(df),
        "lags": lags,
        "target_stk": target_stk,
        "rec_w": rec_w,
        "use_anti": use_anti,
        "blacklist": set(str(x).strip().lstrip("0") or "0" for x in bl),
        "payout": payout,
        "tot_terms": tot_terms
    }

def get_neighbors_wheel(num_str, tot_terms, radius):
    """Devuelve los vecinos numéricos cíclicos en la ruleta (+/- radius)."""
    try:
        val = int(num_str)
    except Exception:
        return [num_str]
    res = []
    for delta in range(-radius, radius + 1):
        n_val = (val + delta) % tot_terms
        res.append(str(n_val))
    return list(set(res))

def simulate_strategy_variant(mode="baseline", extra_lags=0, neighbor_radius=0, max_fichas=None):
    """
    mode:
      - 'baseline': 3 rezagados puros
      - 'neighbors': rezagados + vecinos (+/- neighbor_radius)
      - 'expanded_lags': agregar 1 o 2 lags adicionales
    """
    all_events = []
    
    for r_name, d in preloaded_data.items():
        nums = d["nums"]
        dates = d["dates"]
        horas = d["horas"]
        base_lags = list(d["lags"])
        
        # Si se amplían lags
        if extra_lags == 1:
            lags = base_lags + [base_lags[0] + 7]
        elif extra_lags == 2:
            lags = base_lags + [base_lags[0] + 7, base_lags[1] + 12]
        else:
            lags = base_lags
            
        target_stk = d["target_stk"]
        rec_w = d["rec_w"]
        use_anti = d["use_anti"]
        blacklist = d["blacklist"]
        payout = d["payout"]
        tot_terms = d["tot_terms"]
        
        min_k = max(max(lags), rec_w) + 1
        streak = 0
        cur_d = None
        seen_today = set()
        prev_was_repeat = False
        
        for i in range(min_k, len(nums)):
            act = nums[i]
            dt = dates[i]
            
            if dt != cur_d:
                cur_d = dt
                seen_today = set()
                prev_was_repeat = False
                
            rec_set = set(nums[i - rec_w : i])
            raw_cands = [nums[i - l] for l in lags if i - l >= 0]
            cands_lag = sorted(list((set(raw_cands) - rec_set) - blacklist))
            
            # Construcción de la canasta final de candidatos
            if neighbor_radius > 0 and cands_lag:
                expanded = set()
                for c in cands_lag:
                    for neigh in get_neighbors_wheel(c, tot_terms, neighbor_radius):
                        if neigh not in rec_set and neigh not in blacklist:
                            expanded.add(neigh)
                cands_play = sorted(list(expanded))
            else:
                cands_play = cands_lag
                
            if max_fichas and len(cands_play) > max_fichas:
                cands_play = cands_play[:max_fichas]
                
            skip_anti = bool(use_anti and prev_was_repeat)
            trigger = (streak in target_stk) and (not skip_anti) and (len(cands_play) > 0)
            
            if trigger:
                hit = (act in cands_play)
                cost = len(cands_play) * 1.0  # $1.00 USD plano por ficha
                premio = payout if hit else 0.0
                all_events.append({
                    "hit": hit,
                    "cost": cost,
                    "premio": premio,
                    "pnl": premio - cost
                })
                
            # Racha de seguimiento del núcleo
            if cands_lag and not skip_anti:
                hit_core = (act in cands_lag)
                streak = 0 if hit_core else streak + 1
            elif cands_lag and skip_anti:
                hit_core = (act in cands_lag)
                streak = 0 if hit_core else streak + 1
                
            is_rep = (act in seen_today)
            seen_today.add(act)
            prev_was_repeat = is_rep
            
    df_ev = pd.DataFrame(all_events)
    if df_ev.empty:
        return 0, 0, 0, 0, 0, 0, 0
    ops = len(df_ev)
    hits = len(df_ev[df_ev['hit'] == True])
    wr = (hits / ops * 100)
    inv = df_ev['cost'].sum()
    cob = df_ev['premio'].sum()
    pnl = df_ev['pnl'].sum()
    roi = (pnl / inv * 100) if inv > 0 else 0
    
    # Drawdown
    cum = df_ev['pnl'].cumsum()
    peak = cum.cummax()
    dd = (cum - peak).min()
    avg_fichas = inv / ops if ops > 0 else 0
    return ops, hits, wr, inv, pnl, roi, dd, avg_fichas

print("="*105)
print("EXPERIMENTO CUANTITATIVO: COMPARATIVA DE AMPLIACIÓN DE CANDIDATOS EN PUNTOS CRÍTICOS")
print("="*105)

experimentos = [
    ("1. BASELINE ACTUAL (Canasta Pura 3 Rezagados)", {"mode": "baseline", "extra_lags": 0, "neighbor_radius": 0}),
    ("2. VECINOS RADIUS ±1 (Puntos críticos + 1 vecino a cada lado)", {"mode": "neighbors", "extra_lags": 0, "neighbor_radius": 1}),
    ("3. VECINOS RADIUS ±1 con Cap Máximo 6 Fichas", {"mode": "neighbors", "extra_lags": 0, "neighbor_radius": 1, "max_fichas": 6}),
    ("4. VECINOS RADIUS ±2 (Zona de influencia de 5 números por candidato)", {"mode": "neighbors", "extra_lags": 0, "neighbor_radius": 2}),
    ("5. AMPLIACIÓN DE LAGS: 4 Rezagados (Agregar 1 lag auxiliar)", {"mode": "expanded_lags", "extra_lags": 1, "neighbor_radius": 0}),
    ("6. AMPLIACIÓN DE LAGS: 5 Rezagados (Agregar 2 lags auxiliares)", {"mode": "expanded_lags", "extra_lags": 2, "neighbor_radius": 0}),
]

print(f"{'OPCIÓN / CONFIGURACIÓN':<45} | {'OPS':<5} | {'WR%':<6} | {'FICHAS/OP':<9} | {'INVERSIÓN':<11} | {'PNL NETO':<11} | {'ROI%':<7} | {'MAX DD':<8}")
print("-"*105)

for nombre, params in experimentos:
    ops, hits, wr, inv, pnl, roi, dd, avg_f = simulate_strategy_variant(**params)
    print(f"{nombre:<45} | {ops:<5} | {wr:5.2f}% | {avg_f:<9.1f} | ${inv:<10,.0f} | ${pnl:<10,.1f} | {roi:+6.1f}% | ${dd:<7,.0f}")
