import os
import sys
import json
import math
from collections import defaultdict, Counter
import numpy as np
import pandas as pd
from scipy import stats

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def analyze_roulette(file_path: str, r_name: str, payout: float = 30.0, output_json: str = None):
    print("=" * 80)
    print(f"🔬 MINERÍA PROFUNDA DE PATRONES: {r_name.upper()}")
    print("=" * 80)

    df = pd.read_csv(file_path, dtype={"numero": str})
    df["numero"] = df["numero"].astype(str).str.strip()
    df["animal"] = df["animal"].astype(str).str.strip()
    df["fecha"] = df["fecha"].astype(str).str.strip()
    df["hora"] = df["hora"].astype(str).str.strip()
    df["dia"] = df["dia"].astype(str).str.strip()
    df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
    df = df.dropna(subset=["sort_dt"]).sort_values("sort_dt").reset_index(drop=True)

    N = len(df)
    nums = df["numero"].tolist()
    animals = df["animal"].tolist()
    hours = df["hora"].tolist()
    days = df["dia"].tolist()
    dates = df["fecha"].tolist()

    unique_nums = sorted(list(set(nums)))
    K = len(unique_nums)

    print(f"Total Sorteos Analizados: {N:,} | Rango: {dates[0]} al {dates[-1]}")
    print(f"Universo de Animales (K): {K} | Cuota de Pago: {payout:.0f}x")

    p0 = 1.0 / K
    expected_count = N * p0
    se_global = math.sqrt(N * p0 * (1.0 - p0))

    num_to_name = {}
    for i in range(N):
        num_to_name[nums[i]] = animals[i]

    # 1. UNIFORMIDAD Y CHI-CUADRADO
    counts_global = Counter(nums)
    chi2_stat = 0.0
    z_scores_global = {}

    for num, cnt in counts_global.items():
        dev = cnt - expected_count
        chi2_stat += (dev ** 2) / expected_count
        z_scores_global[num] = dev / se_global

    chi2_pvalue = 1.0 - stats.chi2.cdf(chi2_stat, df=K-1)
    top_hot = sorted(z_scores_global.items(), key=lambda x: x[1], reverse=True)
    top_cold = sorted(z_scores_global.items(), key=lambda x: x[1])

    # 2. HAZARD RATE Y MODELO DE RENOVACIÓN WEIBULL
    last_seen = {}
    gaps = []
    intraday_repeats = 0
    cur_date = None
    seen_today = set()

    for i in range(N):
        d = dates[i]
        n = nums[i]
        if d != cur_date:
            cur_date = d
            seen_today = set()

        if n in seen_today:
            intraday_repeats += 1
        seen_today.add(n)

        if n in last_seen:
            gaps.append(i - last_seen[n])
        last_seen[n] = i

    gaps_arr = np.array(gaps)
    median_gap = np.median(gaps_arr)
    mean_gap = np.mean(gaps_arr)
    shape_weibull, loc_w, scale_w = stats.weibull_min.fit(gaps_arr, floc=0)

    # 3. ESPECTRO DE AUTOCORRELACIÓN Y TOP LAGS
    lag_hit_rates = []
    for l in range(1, 61):
        hits = 0
        trials = 0
        for i in range(l, N):
            trials += 1
            if nums[i] == nums[i - l]:
                hits += 1
        obs_p = hits / trials if trials > 0 else 0
        se_l = math.sqrt(p0 * (1 - p0) / trials)
        z_l = (obs_p - p0) / se_l
        roi_single_lag = (hits * payout - trials) / trials * 100.0
        lag_hit_rates.append({
            "lag": l,
            "hits": hits,
            "trials": trials,
            "observed_wr_pct": round(obs_p * 100.0, 3),
            "expected_wr_pct": round(p0 * 100.0, 3),
            "z_score": round(z_l, 2),
            "roi_pct": round(roi_single_lag, 2)
        })

    top_lags = sorted(lag_hit_rates, key=lambda x: x["z_score"], reverse=True)[:8]
    bottom_lags = sorted(lag_hit_rates, key=lambda x: x["z_score"])[:5]

    # 4. CADENAS DE MARKOV (t-1 -> t)
    transitions = Counter()
    for i in range(1, N):
        transitions[(nums[i-1], nums[i])] += 1

    expected_pair = (N - 1) / (K * K)
    se_pair = math.sqrt((N - 1) * (1.0 / (K * K)) * (1.0 - (1.0 / (K * K))))

    markov_anomalies = []
    for (prev, curr), cnt in transitions.items():
        z_pair = (cnt - expected_pair) / se_pair
        if z_pair >= 3.0:
            markov_anomalies.append({
                "prev_num": prev,
                "prev_anim": num_to_name.get(prev, ""),
                "next_num": curr,
                "next_anim": num_to_name.get(curr, ""),
                "count": cnt,
                "expected": round(expected_pair, 2),
                "z_score": round(z_pair, 2),
                "probability_pct": round(cnt / counts_global[prev] * 100.0, 2)
            })

    markov_anomalies.sort(key=lambda x: x["z_score"], reverse=True)

    # 5. ESTACIONALIDAD HORARIA (CIRCADIANA)
    hora_counts = defaultdict(Counter)
    hora_totals = Counter(hours)
    for i in range(N):
        hora_counts[hours[i]][nums[i]] += 1

    hourly_anomalies = []
    for h, total_h in hora_totals.items():
        exp_h = total_h * p0
        se_h = math.sqrt(total_h * p0 * (1.0 - p0))
        for num, cnt in hora_counts[h].items():
            z_h = (cnt - exp_h) / se_h
            if abs(z_h) >= 2.80:
                hourly_anomalies.append({
                    "hora": h,
                    "numero": num,
                    "animal": num_to_name.get(num, ""),
                    "count": cnt,
                    "expected": round(exp_h, 1),
                    "z_score": round(z_h, 2),
                    "rel_ratio": round(cnt / exp_h, 2)
                })

    hourly_anomalies.sort(key=lambda x: abs(x["z_score"]), reverse=True)

    # 6. ESTACIONALIDAD POR DÍA DE LA SEMANA
    day_totals = Counter(days)
    day_num_counts = defaultdict(Counter)
    for i in range(N):
        day_num_counts[days[i]][nums[i]] += 1

    day_anomalies = []
    for d_name, d_tot in day_totals.items():
        exp_d = d_tot * p0
        se_d = math.sqrt(d_tot * p0 * (1.0 - p0))
        for num, cnt in day_num_counts[d_name].items():
            z_d = (cnt - exp_d) / se_d
            if abs(z_d) >= 2.80:
                day_anomalies.append({
                    "dia": d_name,
                    "numero": num,
                    "animal": num_to_name.get(num, ""),
                    "count": cnt,
                    "expected": round(exp_d, 1),
                    "z_score": round(z_d, 2),
                    "ratio": round(cnt / exp_d, 2)
                })

    day_anomalies.sort(key=lambda x: abs(x["z_score"]), reverse=True)

    # IMPRESIÓN SINTÉTICA
    print("\n--- 1. UNIFORMIDAD GLOBAL ---")
    print(f"Chi2 Stat: {chi2_stat:.2f} (df={K-1}) | p-value: {chi2_pvalue:.5f} | Rechazada: {chi2_pvalue < 0.05}")

    print("\n--- 2. TASA DE FALLO Y MEMORIA WEIBULL ---")
    print(f"Shape Beta: {shape_weibull:.4f} | Gap Medio: {mean_gap:.2f} | Mediana: {median_gap:.1f} | Repetición Intradía: {intraday_repeats/N*100:.2f}%")

    print("\n--- 3. SESGOS GLOBALES POR ANIMAL (TOP EXTREMOS) ---")
    print(f"Top Caliente: #{top_hot[0][0]} {num_to_name[top_hot[0][0]]} ({top_hot[0][1]:+.2f} Z, {counts_global[top_hot[0][0]]} veces)")
    print(f"Top Frío:     #{top_cold[0][0]} {num_to_name[top_cold[0][0]]} ({top_cold[0][1]:+.2f} Z, {counts_global[top_cold[0][0]]} veces)")

    print("\n--- 4. TOP 5 LAGS (+EV) ---")
    for l in top_lags[:5]:
        print(f"  • Lag {l['lag']:>2}: WR={l['observed_wr_pct']:.2f}% (Exp {l['expected_wr_pct']:.2f}%) | Z={l['z_score']:+.2f} | ROI={l['roi_pct']:+.2f}%")

    print("\n--- 5. CADENAS DE MARKOV SIGNIFICATIVAS (t-1 -> t) ---")
    for m in markov_anomalies[:5]:
        print(f"  • #{m['prev_num']} {m['prev_anim']} -> #{m['next_num']} {m['next_anim']}: {m['count']} veces (Exp {m['expected']}) | Z={m['z_score']:+.2f} | Prob: {m['probability_pct']}%")

    print("\n--- 6. ANOMALÍAS CIRCADIANAS (HORARIAS) ---")
    for h in hourly_anomalies[:5]:
        print(f"  • Hora {h['hora']:>8} | #{h['numero']:>2} {h['animal']:<12}: {h['count']} veces (Exp {h['expected']}) | Z={h['z_score']:+.2f} | Ratio: {h['rel_ratio']}x")

    result_data = {
        "roulette": r_name,
        "sample_size": N,
        "date_range": {"start": dates[0], "end": dates[-1]},
        "payout": payout,
        "k_animals": K,
        "chi_square": {
            "statistic": round(chi2_stat, 2),
            "degrees_of_freedom": K - 1,
            "p_value": round(chi2_pvalue, 5),
            "uniformity_rejected": bool(chi2_pvalue < 0.05)
        },
        "weibull_hazard": {
            "shape_beta": round(shape_weibull, 4),
            "scale_lambda": round(scale_w, 2),
            "mean_gap": round(mean_gap, 2),
            "median_gap": round(median_gap, 2)
        },
        "intraday_repeats_pct": round(intraday_repeats / N * 100.0, 2),
        "top_hot": [{"num": n, "animal": num_to_name[n], "count": counts_global[n], "z": round(z, 2)} for n, z in top_hot[:5]],
        "top_cold": [{"num": n, "animal": num_to_name[n], "count": counts_global[n], "z": round(z, 2)} for n, z in top_cold[:5]],
        "top_lags": top_lags,
        "bottom_lags": bottom_lags,
        "markov_transitions": markov_anomalies,
        "hourly_seasonality": hourly_anomalies,
        "day_seasonality": day_anomalies
    }

    if output_json:
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Guardado en: {output_json}")

    return result_data

if __name__ == "__main__":
    file_path = r"C:\Users\victo\nuevas_ruletas\data_vz\la_granjita_2anios.csv"
    output_path = r"C:\Users\victo\nuevas_ruletas\scratch\la_granjita_deep_patterns.json"
    analyze_roulette(file_path, "La Granjita", payout=30.0, output_json=output_path)
