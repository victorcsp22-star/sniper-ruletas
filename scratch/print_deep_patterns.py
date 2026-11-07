import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

with open(r"C:\Users\victo\nuevas_ruletas\scratch\lotto_activo_deep_patterns.json", "r", encoding="utf-8") as f:
    d = json.load(f)

print("--- 1. UNIFORMIDAD GLOBAL Y CHI-CUADRADO ---")
print(f"Chi2 Stat: {d['chi_square']['statistic']}, p-value: {d['chi_square']['p_value']}")
print(f"¿Uniformidad rechazada?: {d['chi_square']['uniformity_rejected']}")

print("\n--- 2. WEIBULL & HAZARD RATE (MEMORIA DE INTERVALO) ---")
print(f"Shape Beta: {d['weibull_hazard']['shape_beta']} -> {d['weibull_hazard']['interpretation']}")
print(f"Gap Medio: {d['weibull_hazard']['mean_gap']} sorteos | Mediana: {d['weibull_hazard']['median_gap']} sorteos")
print(f"Porcentaje de Repeticiones Intradía: {d['intraday_repeats_pct']}%")

print("\n--- 3. SESGOS GLOBALES POR ANIMAL (Z-SCORE) ---")
print("Top Sobre-representados (Calientes):")
for h in d['top_global_deviations']['hot']:
    print(f"  • #{h['num']} {h['animal']}: {h['count']} veces (Z = {h['z']:+.2f})")
print("Top Sub-representados (Fríos):")
for c in d['top_global_deviations']['cold']:
    print(f"  • #{c['num']} {c['animal']}: {c['count']} veces (Z = {c['z']:+.2f})")

print("\n--- 4. AUTOCORRELACIÓN Y LAGS INDIVIDUALES (+EV) ---")
for l in d['top_lags'][:6]:
    print(f"  • Lag {l['lag']:>2}: WR={l['observed_wr_pct']:.2f}% (Exp {l['expected_wr_pct']:.2f}%) | Z={l['z_score']:+.2f} | ROI={l['roi_pct']:+.2f}%")

print("\n--- 5. CADENAS DE MARKOV Y TRANSICIONES CONDICIONALES ANÓMALAS (t-1 -> t) ---")
for m in d['markov_transitions_top'][:8]:
    print(f"  • Tras #{m['prev_num']} {m['prev_anim']} -> Sigue #{m['next_num']} {m['next_anim']}: {m['count']} veces (Esperado {m['expected']}) | Z={m['z_score']:+.2f} | Probabilidad: {m['probability_pct']}%")

print("\n--- 6. RESONANCIA CIRCADIANA (ANOMALÍAS POR HORA) ---")
for h in d['hourly_seasonality_top'][:8]:
    print(f"  • Hora {h['hora']:>8} | #{h['numero']:>2} {h['animal']:<12}: {h['count']} apariciones (Esperado {h['expected']}) | Z={h['z_score']:+.2f} | Ratio: {h['rel_ratio']}x")

print("\n--- 7. ESTACIONALIDAD POR DÍA DE LA SEMANA ---")
for day in d['day_seasonality_top'][:6]:
    print(f"  • {day['dia']:<10} | #{day['numero']:>2} {day['animal']:<12}: {day['count']} apariciones (Esperado {day['expected']}) | Z={day['z_score']:+.2f} | Ratio: {day['ratio']}x")
