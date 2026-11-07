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

FILE_PATH = r"C:\Users\victo\nuevas_ruletas\data_vz\lotto_activo_2anios.csv"
OUTPUT_JSON = r"C:\Users\victo\nuevas_ruletas\scratch\lotto_activo_deep_patterns.json"

df = pd.read_csv(FILE_PATH, dtype={"numero": str})
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

print(f"Dataset analizado: Lotto Activo")
print(f"Total sorteos: {N:,} | Rango: {dates[0]} al {dates[-1]}")
print(f"Total animales únicos identificados (K): {K}")

p0 = 1.0 / K
expected_count = N * p0
se_global = math.sqrt(N * p0 * (1.0 - p0))

# -------------------------------------------------------------
# 1. ANÁLISIS DE FRECUENCIA GLOBAL Y TEST CHI-CUADRADO
# -------------------------------------------------------------
counts_global = Counter(nums)
chi2_stat = 0.0
z_scores_global = {}

for num, cnt in counts_global.items():
    dev = cnt - expected_count
    chi2_stat += (dev ** 2) / expected_count
    z_scores_global[num] = dev / se_global

chi2_pvalue = 1.0 - stats.chi2.cdf(chi2_stat, df=K-1)

# Top sobre-representados y sub-representados (|Z| > 2.0)
top_hot = sorted(z_scores_global.items(), key=lambda x: x[1], reverse=True)
top_cold = sorted(z_scores_global.items(), key=lambda x: x[1])

# Mapeo num a animal
num_to_name = {}
for i in range(N):
    num_to_name[nums[i]] = animals[i]

# -------------------------------------------------------------
# 2. ANÁLISIS DE RESIDENCIA HORARIA (CIRCADIAN SEASONALITY)
# -------------------------------------------------------------
# Frecuencia condicional por hora: P(X | hora)
hora_counts = defaultdict(Counter)
hora_totals = Counter(hours)

for i in range(N):
    h = hours[i]
    n = nums[i]
    hora_counts[h][n] += 1

hourly_anomalies = []
for h, total_h in hora_totals.items():
    exp_h = total_h * p0
    se_h = math.sqrt(total_h * p0 * (1.0 - p0))
    for num, cnt in hora_counts[h].items():
        z_h = (cnt - exp_h) / se_h
        if abs(z_h) >= 2.80:  # Significancia estadística p < 0.005
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

# -------------------------------------------------------------
# 3. CADENAS DE MARKOV Y MATRICES DE TRANSICIÓN DE 1ER ORDEN
# -------------------------------------------------------------
# Pares consecutivos (t-1 -> t)
transitions = Counter()
for i in range(1, N):
    transitions[(nums[i-1], nums[i])] += 1

# Esperanza para cada par (38 x 38 = 1,444 pares)
expected_pair = (N - 1) / (K * K)
se_pair = math.sqrt((N - 1) * (1.0 / (K * K)) * (1.0 - (1.0 / (K * K))))

markov_anomalies = []
for (prev, curr), cnt in transitions.items():
    z_pair = (cnt - expected_pair) / se_pair
    if z_pair >= 3.0:  # Significancia p < 0.0013
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

# -------------------------------------------------------------
# 4. ANÁLISIS DE INTERVALOS ENTRE APARICIONES (RENEWAL & HAZARD RATE)
# -------------------------------------------------------------
# Gaps entre apariciones consecutivas del mismo número
last_seen = {}
gaps = []
intraday_repeats = 0
cur_date = None
seen_today = set()

intraday_gap_counts = Counter()

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
        gap = i - last_seen[n]
        gaps.append(gap)
        if gap <= 12:
            intraday_gap_counts[gap] += 1
    last_seen[n] = i

gaps_arr = np.array(gaps)
median_gap = np.median(gaps_arr)
mean_gap = np.mean(gaps_arr)
std_gap = np.std(gaps_arr)

# Estimación del parámetro de forma Weibull (beta)
# beta = 1 -> Exponencial pura (sin memoria)
# beta > 1 -> Desgaste / envejecimiento (mayor probabilidad con el tiempo)
# beta < 1 -> Agrupamiento / clustering (mayor probabilidad de repetir pronto)
shape_weibull, loc_w, scale_w = stats.weibull_min.fit(gaps_arr, floc=0)

# -------------------------------------------------------------
# 5. ANÁLISIS DE LAGS INTRA-DÍA Y MULTI-DÍA (MÚLTIPLOS DE HORARIO)
# -------------------------------------------------------------
# El horario se repite cada 11 o 12 sorteos (dependiendo si hay sorteo de 8am)
# Analizar rezagos l en el rango [1..60]
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
    roi_single_lag = (hits * 30.0 - trials) / trials * 100.0
    lag_hit_rates.append({
        "lag": l,
        "hits": hits,
        "trials": trials,
        "observed_wr_pct": round(obs_p * 100.0, 3),
        "expected_wr_pct": round(p0 * 100.0, 3),
        "z_score": round(z_l, 2),
        "roi_pct": round(roi_single_lag, 2)
    })

top_lags = sorted(lag_hit_rates, key=lambda x: x["z_score"], reverse=True)[:10]
bottom_lags = sorted(lag_hit_rates, key=lambda x: x["z_score"])[:5]

# -------------------------------------------------------------
# 6. ANÁLISIS POR DÍA DE LA SEMANA (DAY-OF-WEEK SEASONALITY)
# -------------------------------------------------------------
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

# -------------------------------------------------------------
# 7. CONSOLIDACIÓN Y SERIALIZACIÓN DE RESULTADOS
# -------------------------------------------------------------
report_data = {
    "roulette": "Lotto Activo",
    "sample_size": N,
    "date_range": {"start": dates[0], "end": dates[-1]},
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
        "median_gap": round(median_gap, 2),
        "interpretation": "Clustering (<1)" if shape_weibull < 0.95 else ("Aging (>1)" if shape_weibull > 1.05 else "Poisson/Memoryless (~1)")
    },
    "intraday_repeats_pct": round(intraday_repeats / N * 100.0, 2),
    "top_global_deviations": {
        "hot": [{"num": n, "animal": num_to_name[n], "count": counts_global[n], "z": round(z, 2)} for n, z in top_hot[:5]],
        "cold": [{"num": n, "animal": num_to_name[n], "count": counts_global[n], "z": round(z, 2)} for n, z in top_cold[:5]]
    },
    "top_lags": top_lags,
    "bottom_lags": bottom_lags,
    "markov_transitions_top": markov_anomalies[:12],
    "hourly_seasonality_top": hourly_anomalies[:12],
    "day_seasonality_top": day_anomalies[:10]
}

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(report_data, f, indent=2, ensure_ascii=False)

print(f"\n✅ Análisis profundo completado exitosamente. Datos serializados en: {OUTPUT_JSON}")
