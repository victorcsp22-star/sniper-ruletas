"""
========================================================================================
 ANÁLISIS FORENSE PROFUNDO DE ANOMALÍAS EN CHANCE ANIMALITOS A Y B
========================================================================================
Objetivo:
Rastrear hacia dónde se desvía la masa de probabilidad ante el bloqueo artificial 
de repetición inmediata (0.28% observado vs 2.56% teórico).

Hipótesis de investigación:
1. Desvío por Decenas / Sectores: ¿Se concentra en la decena opuesta?
2. Desvío por Paridad / Terminales: ¿Existe correlación par/impar o mismo terminal?
3. Cadenas de Markov de 1er y 2do Orden: ¿Existen transiciones condicionadas 
   (Si sale A -> sale B con probabilidad > 1/30 = 3.33%)?
4. Efecto Espejo o Simetría entre Chance A y Chance B: ¿Se correlacionan entre sí 
   los sorteos que ocurren a la misma hora?
5. Ventana de Retorno (Rebote diferido): Si no repite en t+1, ¿en qué lag (t+2, t+3, t+4) 
   se concentra el exceso de frecuencia compensatoria?
========================================================================================
"""

import os
import pandas as pd
import numpy as np
from collections import defaultdict, Counter

DATA_DIR = r"C:\Users\victo\nuevas_ruletas\data_candidatos"
path_a = os.path.join(DATA_DIR, "chance_con_animalitos_a.csv")
path_b = os.path.join(DATA_DIR, "chance_con_animalitos_b.csv")

df_a = pd.read_csv(path_a)
df_b = pd.read_csv(path_b)

print("=" * 80)
print(f"ANÁLISIS FORENSE DE CHANCE A ({len(df_a):,} sorteos) Y CHANCE B ({len(df_b):,} sorteos)")
print("=" * 80)

def analizar_ruleta(df, nombre):
    nums = df["numero"].astype(int).tolist()
    n = len(nums)
    
    print(f"\n>>> 1. CURVA DE RETORNO Y AUTOCORRELACIÓN POR LAGS ({nombre}):")
    # Frecuencia en que el número actual coincide con el número en lag k
    print(f"{'Lag':<6} | {'Repeticiones':<12} | {'Frecuencia Real':<16} | {'Frecuencia Teórica':<18} | {'Desviación':<10}")
    print("-" * 70)
    teorico = (1.0 / 39.0) * 100.0
    for lag in range(1, 11):
        matches = sum(1 for i in range(lag, n) if nums[i] == nums[i - lag])
        freq = (matches / (n - lag)) * 100.0
        diff = freq - teorico
        sign = "+" if diff > 0 else ""
        print(f"t+{lag:<3} | {matches:<12} | {freq:<15.2f}% | {teorico:<17.2f}% | {sign}{diff:.2f}%")

    print(f"\n>>> 2. TRANSICIÓN POR PARIDAD Y TERMINALES ({nombre}):")
    # Par vs Impar (0 se toma como neutro o según regla)
    pares = sum(1 for x in nums if x % 2 == 0)
    print(f"Balance Global Par / Impar: {pares/n*100:.1f}% Par | {(n-pares)/n*100:.1f}% Impar")
    
    # Probabilidad de alternancia de paridad
    alt_par = sum(1 for i in range(1, n) if (nums[i] % 2) != (nums[i-1] % 2))
    print(f"Tasa de alternancia Par->Impar o Impar->Par: {alt_par/(n-1)*100:.2f}% (Teórico: 50.00%)")

    # Mismo terminal en sorteo consecutivo (ej. 4 -> 14, 24, 34)
    mismo_terminal = sum(1 for i in range(1, n) if (nums[i] % 10) == (nums[i-1] % 10))
    print(f"Mismo terminal consecutivo (Lag 1): {mismo_terminal/(n-1)*100:.2f}% (Teórico: ~10.00%)")

    print(f"\n>>> 3. DETECCIÓN DE CADENAS DE MARKOV CON VENTAJA MATEMÁTICA (> 3.33%):")
    # Umbral de rentabilidad a payout 30x: Necesitamos probabilidad > 1/30 = 3.333%
    # Para tener ventaja (Edge > 10%), requerimos probabilidad > 3.67%
    transiciones = defaultdict(Counter)
    for i in range(1, n):
        prev = nums[i-1]
        cur = nums[i]
        transiciones[prev][cur] += 1

    super_transiciones = []
    for prev, counter in transiciones.items():
        total_salidas = sum(counter.values())
        if total_salidas < 50:
            continue
        for cur, count in counter.most_common(3):
            prob = (count / total_salidas) * 100.0
            edge = prob - (100.0 / 30.0) # Margen sobre el payout 30x
            if prob >= 4.0: # Fuerte anomalía estadística
                super_transiciones.append((prev, cur, count, total_salidas, prob, edge))

    print(f"Total de pares (A -> B) con probabilidad >= 4.00% (Edge positivo neto): {len(super_transiciones)}")
    if super_transiciones:
        print(f"{'Previo':<8} -> {'Siguiente':<9} | {'Apariciones':<12} | {'Probabilidad':<14} | {'Ventaja s/Banca'}")
        print("-" * 65)
        for prev, cur, count, tot, prob, edge in sorted(super_transiciones, key=lambda x: x[4], reverse=True)[:10]:
            print(f"#{prev:<6} -> #{cur:<7} | {count}/{tot:<8} | {prob:<13.2f}% | +{edge:.2f}%")

analizar_ruleta(df_a, "CHANCE CON ANIMALITOS A")
analizar_ruleta(df_b, "CHANCE CON ANIMALITOS B")

# 4. Análisis de Correlación Espejo entre Chance A y Chance B
print("\n" + "=" * 80)
print(">>> 4. CORRELACIÓN ESPÉCULO / SINCRONIZADA ENTRE CHANCE A Y CHANCE B:")
print("=" * 80)

# Unir por fecha y hora
merged = pd.merge(df_a, df_b, on=["fecha", "hora"], suffixes=("_a", "_b"))
print(f"Sorteos coincidentes en misma fecha y hora: {len(merged):,}")

coincidencias_directas = sum(1 for _, row in merged.iterrows() if int(row["numero_a"]) == int(row["numero_b"]))
pct_coincidencias = (coincidencias_directas / len(merged)) * 100.0
print(f"¿Sale el MISMO número a la misma hora en A y B?: {coincidencias_directas} veces ({pct_coincidencias:.2f}%) | Teórico: 2.56%")

# Mismo terminal a la misma hora
mismo_term_ab = sum(1 for _, row in merged.iterrows() if (int(row["numero_a"]) % 10) == (int(row["numero_b"]) % 10))
pct_term_ab = (mismo_term_ab / len(merged)) * 100.0
print(f"¿Mismo terminal a la misma hora entre A y B?: {mismo_term_ab} veces ({pct_term_ab:.2f}%) | Teórico: 10.00%")

# Distancia promedio entre número A y número B
diffs = [abs(int(r["numero_a"]) - int(r["numero_b"])) for _, r in merged.iterrows()]
print(f"Distancia media aritmética |A - B|: {np.mean(diffs):.2f} (Teórico aleatorio: ~13.00)")
