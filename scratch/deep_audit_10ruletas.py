"""
Análisis Multidimensional Profundo de las 10 Ruletas Candidatas:
1. Ruletas evaluadas:
   - Lotto Gato
   - Granja Millonaria Granjazo
   - Loto Chaima
   - Guacharo Activo
   - Mega Animal 40
   - Ruleta Royal
   - Lotto Activo
   - Gatazo
   - Monje Millonario
   - La Granjita (vs reemplazo)
2. Búsqueda de anomalías en:
   - Vector de Lags óptimos reales
   - Atractores de Markov (transiciones mono-animal)
   - Patrón de duplicados del día (Anti-clustering suitability)
   - Gatillo óptimo de racha (¿Es Racha 1, Racha 2 o Racha 0?)
   - Filtrado por horario
"""

import os, collections, pandas as pd, numpy as np

CANDIDATAS = {
    "Lotto Gato": (r"C:\Users\victo\nuevas_ruletas\lotto_gato.csv", 60.0, 75),
    "Granja Mill. Granjazo": (r"C:\Users\victo\nuevas_ruletas\granja_millonaria_granjazo.csv", 60.0, 75),
    "Loto Chaima": (r"C:\Users\victo\nuevas_ruletas\loto_chaima.csv", 60.0, 75),
    "Guacharo Activo": (r"C:\Users\victo\nuevas_ruletas\data_vz\guacharo_activo_2anios.csv", 60.0, 75),
    "Mega Animal 40": (r"C:\Users\victo\nuevas_ruletas\mega_animal_40.csv", 30.0, 40),
    "Ruleta Royal": (r"C:\Users\victo\nuevas_ruletas\data_vz\ruleta_royal_2anios.csv", 30.0, 38),
    "Lotto Activo": (r"C:\Users\victo\nuevas_ruletas\data_vz\lotto_activo_2anios.csv", 30.0, 38),
    "Gatazo": (r"C:\Users\victo\nuevas_ruletas\gatazo.csv", 60.0, 75),
    "Monje Millonario": (r"C:\Users\victo\nuevas_ruletas\monje_millonario.csv", 60.0, 75),
    "La Granjita": (r"C:\Users\victo\nuevas_ruletas\data_vz\la_granjita_2anios.csv", 30.0, 38),
}

def deep_audit_roulette(name, path, payout, total_animals):
    df = pd.read_csv(path)
    if "fecha" in df.columns and "hora" in df.columns:
        df["dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], errors="coerce")
        df = df.sort_values(by="dt").dropna(subset=["numero"]).reset_index(drop=True)
    nums = [str(x).strip() for x in df["numero"].tolist()]
    dates = df["fecha"].astype(str).tolist() if "fecha" in df.columns else [""] * len(nums)
    horas = df["hora"].astype(str).tolist() if "hora" in df.columns else [""] * len(nums)
    N = len(nums)
    p_rand = 1.0 / total_animals

    # 1. MEJORES 5 LAGS
    lag_lifts = []
    for l in range(6, min(55, N - 10)):
        hits = sum(1 for i in range(l, N) if nums[i] == nums[i-l])
        trials = N - l
        r = hits / trials if trials > 0 else 0
        lift = r / p_rand
        lag_lifts.append((l, lift, hits, trials))
    lag_lifts.sort(key=lambda x: x[1], reverse=True)
    top_lags = [x[0] for x in lag_lifts[:5]]
    best_lag_lifts = [round(x[1], 2) for x in lag_lifts[:5]]

    # 2. ANOMALÍA MARKOV (Pares de transición con lift >= 2.5x y frecuencia >= 5)
    pair_counts = collections.defaultdict(int)
    from_counts = collections.defaultdict(int)
    for i in range(1, N):
        pair_counts[(nums[i-1], nums[i])] += 1
        from_counts[nums[i-1]] += 1
    
    strong_markov = []
    for (n1, n2), cnt in pair_counts.items():
        if cnt >= 5:
            cond_prob = cnt / from_counts[n1]
            lift = cond_prob / p_rand
            if lift >= 2.5:
                strong_markov.append((n1, n2, cnt, round(cond_prob*100, 1), round(lift, 2)))
    strong_markov.sort(key=lambda x: x[4], reverse=True)

    # 3. ANOMALÍA POR GATILLO DE RACHA (Buscar cuál racha genera el ROI máximo)
    racha_results = {}
    test_lags = top_lags[:3]
    rec_w = 6
    for t_streak in [0, 1, 2, 3]:
        streak = 0
        ops = 0
        wins = 0
        inv = 0.0
        cob = 0.0
        for i in range(max(test_lags) + rec_w, N):
            actual = nums[i]
            rec_set = set(nums[i-rec_w:i])
            cands = list({nums[i-l] for l in test_lags} - rec_set)
            if streak == t_streak and cands:
                ops += 1
                cost = len(cands) * 1.0
                inv += cost
                hit = actual in cands
                if hit:
                    wins += 1
                    cob += payout * 1.0
            if cands:
                streak = 0 if actual in cands else streak + 1
        
        wr = wins / ops * 100 if ops > 0 else 0
        roi = (cob - inv) / inv * 100 if inv > 0 else 0
        racha_results[t_streak] = {"ops": ops, "wr": round(wr, 1), "roi": round(roi, 1)}

    # 4. DUPLICADOS INTRADÍA
    cur_d = None
    d_draws = []
    dups = 0
    total_intra = 0
    for i in range(N):
        d = dates[i]
        if d != cur_d:
            cur_d = d
            d_draws = []
        else:
            total_intra += 1
            if nums[i] in d_draws:
                dups += 1
        d_draws.append(nums[i])
    dup_pct = dups / total_intra * 100 if total_intra > 0 else 0

    return {
        "name": name,
        "N": N,
        "payout": payout,
        "top_lags": top_lags,
        "best_lag_lifts": best_lag_lifts,
        "markov_count": len(strong_markov),
        "top_markov_sample": strong_markov[:3],
        "racha_results": racha_results,
        "dup_pct": round(dup_pct, 1)
    }

print("=== REVISIÓN PROFUNDA DE ANOMALÍAS EN LAS 10 RULETAS ===")
for name, (path, payout, total_anim) in CANDIDATAS.items():
    res = deep_audit_roulette(name, path, payout, total_anim)
    print(f"\n[{res['name']}] (N={res['N']} sorteos | {res['payout']}x)")
    print(f"  • Top Lags óptimos: {res['top_lags']} (Lifts: {res['best_lag_lifts']})")
    print(f"  • Tasa de duplicados intradía: {res['dup_pct']}% (Anti-clustering: {'Crítico' if res['dup_pct']>12 else 'Normal'})")
    print(f"  • Anomalías Markov fuertes (Lift >= 2.5x): {res['markov_count']} pares detectados")
    if res['top_markov_sample']:
        m_str = ", ".join([f"#{m[0]}->#{m[1]} ({m[2]}x, lift {m[4]}x)" for m in res['top_markov_sample']])
        print(f"    Muestra Markov: {m_str}")
    print(f"  • Comparativa por Racha:")
    for st, vals in res['racha_results'].items():
        print(f"    Racha {st}: {vals['ops']} ops | WR: {vals['wr']}% | ROI: {vals['roi']:+}%")
