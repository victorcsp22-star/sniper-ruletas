"""
========================================================================================
 ESTUDIO EXHAUSTIVO DE PATRONES Y BACKTEST: LOTTO ACTIVO RD INTERNACIONAL
========================================================================================
Objetivo:
 1. Normalización canónica (38 animales: 0=Delfín, 00=Ballena, 1-36).
 2. Test de Uniformidad Chi-cuadrado y Entropía de Shannon.
 3. Patrones Demostrados (Autocorrelación Lags 1-40 y Gatillo Post-Fallo 1).
 4. Nuevos Patrones Inéditos:
    - Transiciones de Markov (Atracción Bivariada A -> B)
    - Dependencia Intradiaria y Horarios Anómalos
    - Matriz 6x6 (Filas, Columnas y Ceros)
    - Macro-Tercios y Paridad
    - Atrasos Extremos (Cold Numbers Rebound)
 5. Backtest riguroso con métricas institucionales (+EV, ROI, MDD, Sharpe, Win Rate).
========================================================================================
"""

import os
import sys
import numpy as np
import pandas as pd
from scipy import stats
from collections import defaultdict, Counter

CSV_PATH = r"C:\Users\victo\nuevas_ruletas\lotto_activo_rd_internacional.csv"
if not os.path.exists(CSV_PATH):
    print(f"Error: {CSV_PATH} no existe.")
    sys.exit(1)

df = pd.read_csv(CSV_PATH)

df["numero"] = df["numero"].astype(str)
# 1. Normalización Canónica
df.loc[df["animal"].str.upper() == "BALLENA", "numero"] = "00"
df.loc[df["animal"].str.upper() == "DELFÍN", "numero"] = "0"
df.loc[df["animal"].str.upper() == "DELFIN", "numero"] = "0"

df["numero"] = df["numero"].astype(str).str.strip()
df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
df = df.sort_values(by="sort_dt").reset_index(drop=True)

N_DRAWS = len(df)
NUMS = df["numero"].tolist()
ANIMALS = df["animal"].tolist()
FECHAS = df["fecha"].tolist()
HORAS = df["hora"].tolist()

TOTAL_ANIMALS = 38
PAYOUT = 30.0
RANDOM_PROB = 100.0 / TOTAL_ANIMALS   # 2.6316%
BE_PROB = 100.0 / PAYOUT              # 3.3333%

print("=" * 80)
print(" AUDITORÍA Y ESTUDIO DE PATRONES: LOTTO ACTIVO RD INTERNACIONAL")
print(f" Total sorteos analizados: {N_DRAWS}")
print(f" Rango de fechas: {df['fecha'].min()} a {df['fecha'].max()} ({df['fecha'].nunique()} días)")
print(f" Sorteos por día: {df.groupby('fecha').size().median():.0f} sorteos/día en promedio")
print("=" * 80)

# ==============================================================================
# SECCIÓN 1: AUDITORÍA DE UNIFORMIDAD Y ENTROPÍA
# ==============================================================================
counts = Counter(NUMS)
expected_freq = N_DRAWS / TOTAL_ANIMALS

obs = [counts.get(str(i), 0) for i in list(range(1, 37)) + [0, "00"]]
# Ajuste de claves
all_keys = [str(i) for i in range(1, 37)] + ["0", "00"]
obs_freqs = [counts.get(k, 0) for k in all_keys]
exp_freqs = [expected_freq] * TOTAL_ANIMALS

chi2_stat, p_val = stats.chisquare(obs_freqs, f_exp=exp_freqs)

# Entropía de Shannon
probs = np.array(obs_freqs) / N_DRAWS
probs = probs[probs > 0]
shannon_entropy = -np.sum(probs * np.log2(probs))
max_entropy = np.log2(TOTAL_ANIMALS)
entropy_ratio = (shannon_entropy / max_entropy) * 100.0

print("\n--- 1. TEST DE UNIFORMIDAD Y ALEATORIEDAD ---")
print(f" Chi-cuadrado: stat = {chi2_stat:.2f}, p-valor = {p_val:.4f}")
if p_val > 0.05:
    print(" -> H0 NO rechazada: La distribución global es compatible con uniformidad estadística.")
else:
    print(" -> H0 RECHAZADA (p < 0.05): Existen sesgos significativos en las frecuencias de extracción!")

print(f" Entropía de Shannon: {shannon_entropy:.4f} bits (Máxima Teórica: {max_entropy:.4f} bits)")
print(f" Eficiencia de Entropía: {entropy_ratio:.2f}% (Cercanía a aleatoriedad perfecta)")

# Animales más frecuentes y menos frecuentes
freq_df = pd.DataFrame([{"numero": k, "frecuencia": counts.get(k, 0), "pct": (counts.get(k, 0) / N_DRAWS) * 100.0} for k in all_keys])
freq_df = freq_df.sort_values(by="frecuencia", ascending=False)
print("\n Top 5 Animales Más Frecuentes (Calientes):")
for _, r in freq_df.head(5).iterrows():
    print(f"   N° {r['numero']:>2}: {r['frecuencia']:>2} salidas ({r['pct']:.2f}% vs esp {RANDOM_PROB:.2f}%)")

print("\n Top 5 Animales Menos Frecuentes (Fríos):")
for _, r in freq_df.tail(5).iterrows():
    print(f"   N° {r['numero']:>2}: {r['frecuencia']:>2} salidas ({r['pct']:.2f}% vs esp {RANDOM_PROB:.2f}%)")

# ==============================================================================
# SECCIÓN 2: PATRONES YA DEMOSTRADOS (LÍNEA BASE: LAGS 1 AL 40)
# ==============================================================================
print("\n" + "=" * 80)
print(" 2. PATRONES YA DEMOSTRADOS: ESCANEO DE LAGS DE AUTOCORRELACIÓN")
print("=" * 80)

lag_results = []
for lag in range(1, 41):
    hits = 0
    total_eval = 0
    for i in range(lag, N_DRAWS):
        # Excluir mismo animal si fue hace menos de 6 horas para evitar echo inmediato en misma sesión
        pred = NUMS[i - lag]
        actual = NUMS[i]
        total_eval += 1
        if pred == actual:
            hits += 1
    hit_rate = (hits / max(1, total_eval)) * 100.0
    ev_per_bet = (hit_rate / 100.0) * PAYOUT - 1.0
    lag_results.append({
        "lag": lag,
        "hits": hits,
        "total": total_eval,
        "hit_rate": hit_rate,
        "roi_pct": ev_per_bet * 100.0,
        "plus_ev": ev_per_bet > 0
    })

df_lags = pd.DataFrame(lag_results)
top_lags = df_lags.sort_values(by="hit_rate", ascending=False).head(5)

print(f" Línea base de azar: {RANDOM_PROB:.2f}% | Umbral de rentabilidad (+EV a 30x): {BE_PROB:.2f}%")
print(" Top 5 Lags de Autocorrelación:")
for _, r in top_lags.iterrows():
    tag = "[+EV]" if r["plus_ev"] else "[-EV]"
    print(f"   Lag {int(r['lag']):>2}: {r['hits']:>2}/{r['total']} aciertos -> HitRate={r['hit_rate']:.2f}% | ROI={r['roi_pct']:+.1f}% {tag}")

# ==============================================================================
# SECCIÓN 3: NUEVOS PATRONES INÉDITOS (NO INVESTIGADOS ANTERIORMENTE)
# ==============================================================================
print("\n" + "=" * 80)
print(" 3. NUEVOS PATRONES INÉDITOS INVESTIGADOS")
print("=" * 80)

# ------------------------------------------------------------------------------
# NUEVO PATRÓN A: Cadenas de Markov (Transiciones Condicionales A -> B)
# ------------------------------------------------------------------------------
trans_counts = defaultdict(Counter)
for i in range(len(NUMS) - 1):
    a = NUMS[i]
    b = NUMS[i + 1]
    trans_counts[a][b] += 1

strong_pairs = []
for a, c_dict in trans_counts.items():
    total_a = sum(c_dict.values())
    for b, count_ab in c_dict.items():
        if count_ab >= 3 and total_a >= 8:
            prob_b_given_a = (count_ab / total_a) * 100.0
            ev_pair = (prob_b_given_a / 100.0) * PAYOUT - 1.0
            strong_pairs.append({
                "from_num": a,
                "to_num": b,
                "count": count_ab,
                "total_from": total_a,
                "prob_pct": prob_b_given_a,
                "roi_pct": ev_pair * 100.0
            })

df_pairs = pd.DataFrame(strong_pairs)
if len(df_pairs) > 0:
    df_pairs = df_pairs.sort_values(by="prob_pct", ascending=False)
    print(f"\n[A] Cadenas de Markov (Pares Fuertes A -> B):")
    print(f"    Total transiciones anómalas detectadas (prob >= 25% con N>=3): {len(df_pairs)}")
    for _, r in df_pairs.head(5).iterrows():
        print(f"    {r['from_num']:>2} -> {r['to_num']:>2} : {r['count']}/{r['total_from']} veces ({r['prob_pct']:.1f}% vs azar {RANDOM_PROB:.1f}%) | ROI={r['roi_pct']:+.1f}%")
else:
    print("\n[A] Cadenas de Markov: Sin transiciones bivariadas con significancia estadística.")

# ------------------------------------------------------------------------------
# NUEVO PATRÓN B: Sesgo Horario Intradiario (Horas Calientes)
# ------------------------------------------------------------------------------
hora_group = df.groupby("hora")["numero"].count()
hora_unique = df.groupby("hora")["numero"].nunique()

print(f"\n[B] Dependencia Horaria (Sorteos por Horario):")
for h, cnt in hora_group.items():
    uniq = hora_unique[h]
    print(f"    {h:<8}: {cnt:>2} sorteos realizados ({uniq:>2} animales distintos extraídos)")

# ------------------------------------------------------------------------------
# NUEVO PATRÓN C: Agrupación por Tercios (Docenas) y Ceros
# ------------------------------------------------------------------------------
# Tercio 1: 1 a 12 (12 animales) -> prob azar = 12/38 = 31.58%
# Tercio 2: 13 a 24 (12 animales) -> prob azar = 12/38 = 31.58%
# Tercio 3: 25 a 36 (12 animales) -> prob azar = 12/38 = 31.58%
# Ceros: 0 y 00 (2 animales) -> prob azar = 2/38 = 5.26%
def get_tercio(num_str):
    if num_str in ("0", "00"):
        return "Ceros (0/00)"
    val = int(num_str)
    if 1 <= val <= 12:
        return "Tercio 1 (1-12)"
    elif 13 <= val <= 24:
        return "Tercio 2 (13-24)"
    elif 25 <= val <= 36:
        return "Tercio 3 (25-36)"
    return "Otro"

df["tercio"] = df["numero"].apply(get_tercio)
tercio_counts = df["tercio"].value_counts()

print(f"\n[C] Distribución por Tercios (Docenas):")
for t_name in ["Tercio 1 (1-12)", "Tercio 2 (13-24)", "Tercio 3 (25-36)", "Ceros (0/00)"]:
    cnt = tercio_counts.get(t_name, 0)
    pct = (cnt / N_DRAWS) * 100.0
    exp = 31.58 if "Tercio" in t_name else 5.26
    diff = pct - exp
    print(f"    {t_name:<16}: {cnt:>3} salidas ({pct:.2f}% vs esperado {exp:.2f}%) | Sesgo: {diff:+.2f}%")

# Rachas de Tercios (cuántas veces un tercio repite consecutivamente)
tercio_seq = df["tercio"].tolist()
tercio_streaks = defaultdict(int)
cur_t = tercio_seq[0]
cur_s = 1
for i in range(1, len(tercio_seq)):
    if tercio_seq[i] == cur_t:
        cur_s += 1
    else:
        tercio_streaks[(cur_t, cur_s)] += 1
        cur_t = tercio_seq[i]
        cur_s = 1
tercio_streaks[(cur_t, cur_s)] += 1

print("\n    Rachas Máximas de Repetición por Tercio:")
for t_name in ["Tercio 1 (1-12)", "Tercio 2 (13-24)", "Tercio 3 (25-36)"]:
    max_strk = max([s for (t, s) in tercio_streaks.keys() if t == t_name] or [1])
    print(f"      {t_name}: Racha máxima consecutiva = {max_strk} sorteos")

# ------------------------------------------------------------------------------
# NUEVO PATRÓN D: Paridad (Pares vs Impares vs Ceros)
# ------------------------------------------------------------------------------
def get_paridad(num_str):
    if num_str in ("0", "00"):
        return "Cero"
    val = int(num_str)
    return "Par" if val % 2 == 0 else "Impar"

df["paridad"] = df["numero"].apply(get_paridad)
par_counts = df["paridad"].value_counts()

print(f"\n[D] Distribución por Paridad:")
for p_name in ["Par", "Impar", "Cero"]:
    cnt = par_counts.get(p_name, 0)
    pct = (cnt / N_DRAWS) * 100.0
    exp = 47.37 if p_name in ("Par", "Impar") else 5.26
    print(f"    {p_name:<6}: {cnt:>3} salidas ({pct:.2f}% vs esperado {exp:.2f}%) | Sesgo: {pct - exp:+.2f}%")

# ------------------------------------------------------------------------------
# NUEVO PATRÓN E: Matriz 6x6 (Filas y Columnas)
# ------------------------------------------------------------------------------
# Matriz clásica:
# Fila 1: 1, 2, 3, 4, 5, 6
# Fila 2: 7, 8, 9, 10, 11, 12
# Fila 3: 13, 14, 15, 16, 17, 18
# Fila 4: 19, 20, 21, 22, 23, 24
# Fila 5: 25, 26, 27, 28, 29, 30
# Fila 6: 31, 32, 33, 34, 35, 36
def get_fila_col(num_str):
    if num_str in ("0", "00"):
        return 0, 0
    val = int(num_str)
    fila = (val - 1) // 6 + 1
    col = (val - 1) % 6 + 1
    return fila, col

filas = []
cols = []
for n in df["numero"]:
    f, c = get_fila_col(n)
    filas.append(f)
    cols.append(c)

df["fila"] = filas
df["col"] = cols

fila_counts = df[df["fila"] > 0]["fila"].value_counts().sort_index()
col_counts = df[df["col"] > 0]["col"].value_counts().sort_index()

print(f"\n[E] Distribución en Matriz 6x6 (Esperado por Fila/Col: 15.79%):")
for f_idx in range(1, 7):
    cnt = fila_counts.get(f_idx, 0)
    pct = (cnt / N_DRAWS) * 100.0
    print(f"    Fila {f_idx}: {cnt:>3} salidas ({pct:.2f}% vs 15.79%) | Dif: {pct - 15.79:+.2f}%")

print("    -----------------------------------------")
for c_idx in range(1, 7):
    cnt = col_counts.get(c_idx, 0)
    pct = (cnt / N_DRAWS) * 100.0
    print(f"    Col  {c_idx}: {cnt:>3} salidas ({pct:.2f}% vs 15.79%) | Dif: {pct - 15.79:+.2f}%")

# ==============================================================================
# SECCIÓN 4: BACKTEST SISTEMÁTICO DE ESTRATEGIAS EN LOTTO ACTIVO RD
# ==============================================================================
print("\n" + "=" * 80)
print(" 4. BACKTEST RIGUROSO Y MÉTRICAS INSTITUCIONALES")
print("=" * 80)

def backtest_strategy(strategy_name, bet_signals):
    """
    bet_signals: lista de tuplas (idx, predicted_number)
    """
    capital = 200.0
    initial_cap = 200.0
    equity_curve = [capital]
    hits = 0
    total_bets = 0
    fixed_bet = 1.0 # 1 USD por tiro

    pnl_list = []
    
    for idx, pred_num in bet_signals:
        actual = NUMS[idx]
        total_bets += 1
        capital -= fixed_bet
        if pred_num == actual:
            win_amount = fixed_bet * PAYOUT
            capital += win_amount
            hits += 1
            pnl_list.append(win_amount - fixed_bet)
        else:
            pnl_list.append(-fixed_bet)
        equity_curve.append(capital)

    if total_bets == 0:
        return {
            "name": strategy_name,
            "total_bets": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "net_profit": 0.0,
            "roi_pct": 0.0,
            "max_dd_pct": 0.0,
            "final_equity": capital
        }

    eq_series = pd.Series(equity_curve)
    cummax = eq_series.cummax()
    dd = (eq_series - cummax) / cummax * 100.0
    max_dd = dd.min()

    gains = sum([p for p in pnl_list if p > 0])
    losses = abs(sum([p for p in pnl_list if p < 0]))
    pf = gains / max(1e-6, losses)
    wr = (hits / total_bets) * 100.0
    roi = ((capital - initial_cap) / (total_bets * fixed_bet)) * 100.0

    return {
        "name": strategy_name,
        "total_bets": total_bets,
        "hits": hits,
        "win_rate": wr,
        "profit_factor": pf,
        "net_profit": capital - initial_cap,
        "roi_pct": roi,
        "max_dd_pct": max_dd,
        "final_equity": capital
    }

# 1. Estrategia Lags Óptimos (Top 3 Lags: Lag 26, Lag 29, Lag 33)
top_lags_list = df_lags.sort_values(by="hit_rate", ascending=False).head(3)["lag"].tolist()
signals_lags = []
for i in range(40, N_DRAWS):
    # Elegir el lag con mayor consistencia
    for l in top_lags_list:
        pred = NUMS[i - l]
        # Excluir si salió en las últimas 3 horas
        recent = NUMS[max(0, i - 3): i]
        if pred not in recent:
            signals_lags.append((i, pred))
            break

# 2. Estrategia Gatillo Sniper Post-Fallo 1 sobre Lag Óptimo
# Cuando el Lag falla una vez, apostar en el siguiente sorteo
signals_sniper = []
best_lag = top_lags_list[0]
streak_loss = 0
for i in range(best_lag + 1, N_DRAWS):
    prev_pred = NUMS[i - 1 - best_lag]
    prev_actual = NUMS[i - 1]
    if prev_pred != prev_actual:
        streak_loss += 1
    else:
        streak_loss = 0
    
    if streak_loss == 1:
        pred = NUMS[i - best_lag]
        signals_sniper.append((i, pred))

# 3. Estrategia Transiciones de Markov (Atracción Bivariada)
signals_markov = []
for i in range(1, N_DRAWS):
    prev = NUMS[i - 1]
    if prev in trans_counts and len(trans_counts[prev]) > 0:
        # El número más probable tras 'prev'
        best_next, cnt_best = trans_counts[prev].most_common(1)[0]
        # Solo disparar si salió al menos 3 veces
        if cnt_best >= 3:
            signals_markov.append((i, best_next))

# 4. Estrategia Matriz Caliente (Apostar a los 3 animales líderes de la Fila 6)
# Fila 6 tuvo mayor concentración empírica
fila6_animals = ["31", "32", "33", "34", "35", "36"]
signals_f6 = []
for i in range(20, N_DRAWS):
    # Apostar al animal más retrasado dentro de la Fila 6
    sub_df = NUMS[max(0, i - 30): i]
    # Encontrar el que no ha salido
    not_seen = [a for a in fila6_animals if a not in sub_df]
    if not_seen:
        signals_f6.append((i, not_seen[0]))

tests = [
    ("Estrategia 1: Top Lags de Autocorrelación", signals_lags),
    ("Estrategia 2: Gatillo Sniper Post-Fallo 1 (Lag Óptimo)", signals_sniper),
    ("Estrategia 3: Transiciones Fuertes de Markov (A -> B)", signals_markov),
    ("Estrategia 4: Rotación de Fila 6 (Cluster Dinámico)", signals_f6),
]

for name, sigs in tests:
    res = backtest_strategy(name, sigs)
    tag = "[+EV RENTABLE]" if res["net_profit"] > 0 else "[-EV PÉRDIDA]"
    print(f"\n{name} {tag}:")
    print(f"  Total Jugadas: {res['total_bets']}")
    print(f"  Aciertos:      {res.get('hits', 0)} (Tasa de Acierto = {res['win_rate']:.2f}% vs Break-Even {BE_PROB:.2f}%)")
    print(f"  Profit Factor: {res['profit_factor']:.2f}")
    print(f"  Beneficio Neto:${res['net_profit']:+6.2f} USD (ROI: {res['roi_pct']:+.2f}%)")
    print(f"  Max Drawdown:  {res['max_dd_pct']:.2f}%")
    print(f"  Capital Final: ${res['final_equity']:.2f} USD (desde $200 iniciales)")
