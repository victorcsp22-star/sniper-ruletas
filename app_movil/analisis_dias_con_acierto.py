import os, sys
import pandas as pd
from analisis_detallado_opcion5 import df_dias as df_dias_op5
from test_pure_bot_master import df_ev as df_base

# 1. Analizar Opción 5 (4 Lags)
tot_dias_op5 = len(df_dias_op5)
dias_con_acierto_op5 = len(df_dias_op5[df_dias_op5['hits'] >= 1])
dias_cero_acierto_op5 = len(df_dias_op5[df_dias_op5['hits'] == 0])

# 2. Analizar Baseline Actual (3 Lags)
dias_base_summary = []
for f, grp in df_base.groupby('fecha'):
    hits = len(grp[grp['hit'] == True])
    dias_base_summary.append({"fecha": f, "hits": hits})
df_dias_base = pd.DataFrame(dias_base_summary)

tot_dias_base = len(df_dias_base)
dias_con_acierto_base = len(df_dias_base[df_dias_base['hits'] >= 1])
dias_cero_acierto_base = len(df_dias_base[df_dias_base['hits'] == 0])

print("="*80)
print("COMPARATIVA DE FRECUENCIA DE ACIERTOS DIARIOS (2 AÑOS DE HISTORIAL)")
print("="*80)

print("\n>>> OPCIÓN 5 (4 Rezagados - Ampliada):")
print(f"• Total días operados:                 {tot_dias_op5} días")
print(f"• Días CON AL MENOS 1 ACIERTO (≥ 1 hit): {dias_con_acierto_op5} días ({dias_con_acierto_op5/tot_dias_op5*100:.2f}%)")
print(f"• Días con 0 aciertos:                 {dias_cero_acierto_op5} días ({dias_cero_acierto_op5/tot_dias_op5*100:.2f}%)")

print("\n>>> BASELINE ACTUAL (3 Rezagados - Núcleo Actual):")
print(f"• Total días operados:                 {tot_dias_base} días")
print(f"• Días CON AL MENOS 1 ACIERTO (≥ 1 hit): {dias_con_acierto_base} días ({dias_con_acierto_base/tot_dias_base*100:.2f}%)")
print(f"• Días con 0 aciertos:                 {dias_cero_acierto_base} días ({dias_cero_acierto_base/tot_dias_base*100:.2f}%)")

print("\n--- DISTRIBUCIÓN DE ACIERTOS POR DÍA EN OPCIÓN 5 ---")
conteo_hits = df_dias_op5['hits'].value_counts().sort_index()
for h, count in conteo_hits.items():
    pct = count / tot_dias_op5 * 100
    print(f"• {h:2d} aciertos en el día: {count:3d} días ({pct:5.2f}%)")
