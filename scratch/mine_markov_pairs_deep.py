import os
import sys
import json
import math
import pandas as pd
import numpy as np
from collections import defaultdict

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = r"C:\Users\victo\nuevas_ruletas"
VZ_DIR = os.path.join(ROOT_DIR, "data_vz")

RULETAS = {
    "Lotto Activo": {
        "file": os.path.join(VZ_DIR, "lotto_activo_2anios.csv"),
        "k": 38,
        "payout": 30.0
    },
    "La Granjita": {
        "file": os.path.join(VZ_DIR, "la_granjita_2anios.csv"),
        "k": 38,
        "payout": 30.0
    },
    "Ruleta Royal": {
        "file": os.path.join(VZ_DIR, "ruleta_royal_2anios.csv"),
        "k": 38,
        "payout": 30.0
    },
    "Guacharo Activo": {
        "file": os.path.join(VZ_DIR, "guacharo_activo_2anios.csv"),
        "k": 77,
        "payout": 60.0
    },
    "Gatazo": {
        "file": os.path.join(ROOT_DIR, "gatazo.csv"),
        "k": 85,
        "payout": 60.0
    },
    "Mega Animal 40": {
        "file": os.path.join(ROOT_DIR, "mega_animal_40.csv"),
        "k": 47,
        "payout": 30.0
    },
    "Monje Millonario": {
        "file": os.path.join(ROOT_DIR, "monje_millonario.csv"),
        "k": 77,
        "payout": 60.0
    }
}

results_by_roulette = {}

for r_name, cfg in RULETAS.items():
    df = pd.read_csv(cfg["file"], dtype={"numero": str})
    df["numero"] = df["numero"].astype(str).str.strip()
    df["animal"] = df["animal"].astype(str).str.strip()
    df["fecha"] = df["fecha"].astype(str).str.strip()
    df["hora"] = df["hora"].astype(str).str.strip()
    df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
    df = df.dropna(subset=["sort_dt"]).sort_values("sort_dt").reset_index(drop=True)

    nums = df["numero"].tolist()
    animals = df["animal"].tolist()
    num_to_anim = {}
    for n, a in zip(nums, animals):
        num_to_anim[n] = a

    total_draws = len(nums)
    k = cfg["k"]
    p0 = 1.0 / k
    payout = cfg["payout"]

    # Matrices de transicion
    trans_counts = defaultdict(lambda: defaultdict(int))
    count_prev = defaultdict(int)

    # Matriz para memoria selectiva (ultimos 500 sorteos)
    recent_window = min(500, total_draws // 3)
    recent_start = total_draws - recent_window
    recent_trans = defaultdict(lambda: defaultdict(int))
    recent_prev = defaultdict(int)

    for i in range(1, total_draws):
        prev_n = nums[i - 1]
        act_n = nums[i]
        trans_counts[prev_n][act_n] += 1
        count_prev[prev_n] += 1

        if i >= recent_start:
            recent_trans[prev_n][act_n] += 1
            recent_prev[prev_n] += 1

    pairs = []
    for prev_n, next_dict in trans_counts.items():
        n_prev = count_prev[prev_n]
        if n_prev < 15:  # Filtro de significancia minima
            continue

        for act_n, count_pair in next_dict.items():
            if count_pair < 3:
                continue

            prob = count_pair / n_prev
            se = math.sqrt(p0 * (1.0 - p0) / n_prev) if n_prev > 0 else 0.01
            z_score = (prob - p0) / se if se > 0 else 0.0
            ev = (prob * payout) - 1.0

            # Memoria selectiva reciente
            r_prev = recent_prev.get(prev_n, 0)
            r_pair = recent_trans.get(prev_n, {}).get(act_n, 0)
            r_prob = (r_pair / r_prev) if r_prev >= 3 else prob
            r_ev = (r_prob * payout) - 1.0

            # Filtramos transiciones fuertemente anómalas (+EV sustancial y Z >= 2.5)
            if z_score >= 2.50 and ev > 0.15:
                pairs.append({
                    "from_num": prev_n,
                    "from_animal": num_to_anim.get(prev_n, ""),
                    "to_num": act_n,
                    "to_animal": num_to_anim.get(act_n, ""),
                    "count": count_pair,
                    "total_prev": n_prev,
                    "prob": round(prob * 100.0, 2),
                    "prob_base": round(p0 * 100.0, 2),
                    "lift": round(prob / p0, 2),
                    "z_score": round(z_score, 2),
                    "ev_pct": round(ev * 100.0, 2),
                    "recent_count": r_pair,
                    "recent_total_prev": r_prev,
                    "recent_prob": round(r_prob * 100.0, 2),
                    "recent_ev_pct": round(r_ev * 100.0, 2),
                    "is_active_recently": bool(r_pair > 0 and r_ev > 0.0)
                })

    pairs.sort(key=lambda x: (x["z_score"], x["ev_pct"]), reverse=True)
    results_by_roulette[r_name] = {
        "total_draws": total_draws,
        "k": k,
        "payout": payout,
        "top_pairs": pairs[:15]
    }

print("=" * 110)
print("🔍 ESCANEO DE TRANSICIONES SECUENCIALES 'SALE CASI SIEMPRE LUEGO DE OTRO' (MARKOV ORDER 1)")
print("=" * 110)

summary_clean = {}

for r_name, d in results_by_roulette.items():
    print(f"\n🎲 {r_name} ({d['total_draws']} sorteos | Cuota: {d['payout']}x | Base: {100.0/d['k']:.2f}%):")
    pairs = d["top_pairs"]
    if not pairs:
        print("   (Sin transiciones que superen el umbral Z >= 2.50 y EV > +15%)")
        continue

    print(f"   {'PRECURSOR':<22} -> {'CONSECUENTE':<22} | {'PROB':<7} | {'BASE':<6} | {'LIFT':<6} | {'Z-SCORE':<7} | {'EV (%)':<8} | {'MEMORIA REC':<12}")
    print("   " + "-" * 100)
    selected_for_system = []
    for p in pairs:
        active_tag = "🟢 VIGENTE" if p["is_active_recently"] else "🟡 HISTÓRICO"
        print(f"   #{p['from_num']} {p['from_animal']:<17} -> #{p['to_num']} {p['to_animal']:<17} | {p['prob']:.1f}%  | {p['prob_base']:.1f}% | {p['lift']:.2f}x | Z={p['z_score']:+.2f} | {p['ev_pct']:+.1f}%  | {active_tag}")
        if p["z_score"] >= 3.0 and p["is_active_recently"]:
            selected_for_system.append(p)
    summary_clean[r_name] = selected_for_system

with open(os.path.join(ROOT_DIR, "scratch", "markov_selective_memory_pairs.json"), "w", encoding="utf-8") as f:
    json.dump(results_by_roulette, f, indent=2, ensure_ascii=False)
