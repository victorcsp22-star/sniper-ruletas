"""
Generación de gráficos para el Laboratorio Sandbox de Lotto Brasil y Lotto Bicho.
Crea una figura multipanel con:
1. Curva de probabilidad empírica por Lag (1 a 40) mostrando la supresión y los picos circadianos (12, 24, 25, 36).
2. Curvas de crecimiento de capital ($1,000 USD) bajo Grossman-Zhou y Full Kelly.
3. Comparativa de EV y Win Rate vs Umbrales de Break-Even.
"""

import os
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from deep_sandbox_analysis import run_full_deep_sandbox, LOTTERIES

ARTIFACT_DIR = r"C:\Users\victo\.gemini\antigravity\brain\b416ad84-eb18-4af1-a597-d96da11175e8"
OUTPUT_PNG = os.path.join(ARTIFACT_DIR, "grafica_lottobichos_sandbox.png")

results = run_full_deep_sandbox()

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle("LABORATORIO SANDBOX AISLADO: ANÁLISIS CUANTITATIVO LOTTO BRASIL Y LOTTO BICHO\n(Historial 2 Años: 2024 - 2026 | 8,633 Sorteos Oficiales)", fontsize=15, fontweight='bold', y=0.98)

# Panel 1: Espectro de Lags Lotto Brasil
ax1 = axes[0, 0]
df_b = results["lottobrasil"]["df_lags"]
lags = df_b["lag"]
probs_filt = df_b["pct_filt"]
be_brasil = 100.0 / 37.0

ax1.axhspan(0, 1.5, color='red', alpha=0.15, label='Zona de Supresión (Lags 1-6)')
ax1.axhline(100.0/38.0, color='gray', linestyle='--', linewidth=1.5, label='Azar Uniforme (2.63%)')
ax1.axhline(be_brasil, color='green', linestyle=':', linewidth=1.8, label=f'Break-Even 37x ({be_brasil:.2f}%)')
ax1.plot(lags, probs_filt, color='#009c3b', marker='o', markersize=4, linewidth=2, label='Probabilidad Filtrada (Recencia > 6)')

# Resaltar picos 12, 24, 36
for l_peak in [12, 24, 25, 36]:
    val = df_b.loc[df_b["lag"] == l_peak, "pct_filt"].values[0]
    ax1.scatter([l_peak], [val], color='#ffdf00', edgecolors='black', s=90, zorder=5)
    ax1.annotate(f"Lag {l_peak}\n({val:.2f}%)", (l_peak, val), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=8, fontweight='bold')

ax1.set_title("🇧🇷 Lotto Brasil: Espectro de Memoria y Rebotes (Lags 1-40)", fontweight='bold')
ax1.set_xlabel("Lag (Sorteos anteriores)")
ax1.set_ylabel("Probabilidad de Acierto Filtrada (%)")
ax1.set_xlim(1, 40)
ax1.set_ylim(0, 4.5)
ax1.grid(True, linestyle='--', alpha=0.5)
ax1.legend(loc='lower right', fontsize=8)

# Panel 2: Espectro de Lags Lotto Bicho
ax2 = axes[0, 1]
df_bi = results["lottobicho"]["df_lags"]
lags_bi = df_bi["lag"]
probs_filt_bi = df_bi["pct_filt"]
be_bicho = 100.0 / 35.0

ax2.axhspan(0, 1.5, color='red', alpha=0.15, label='Zona de Supresión (Lags 1-6)')
ax2.axhline(100.0/38.0, color='gray', linestyle='--', linewidth=1.5, label='Azar Uniforme (2.63%)')
ax2.axhline(be_bicho, color='darkorange', linestyle=':', linewidth=1.8, label=f'Break-Even 35x ({be_bicho:.2f}%)')
ax2.plot(lags_bi, probs_filt_bi, color='#ff6f00', marker='s', markersize=4, linewidth=2, label='Probabilidad Filtrada (Recencia > 6)')

for l_peak in [12, 13, 25, 26]:
    val = df_bi.loc[df_bi["lag"] == l_peak, "pct_filt"].values[0]
    ax2.scatter([l_peak], [val], color='#00e676', edgecolors='black', s=90, zorder=5)
    ax2.annotate(f"Lag {l_peak}\n({val:.2f}%)", (l_peak, val), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=8, fontweight='bold')

ax2.set_title("🐆 Lotto Bicho: Espectro de Memoria y Rebotes (Lags 1-40)", fontweight='bold')
ax2.set_xlabel("Lag (Sorteos anteriores)")
ax2.set_ylabel("Probabilidad de Acierto Filtrada (%)")
ax2.set_xlim(1, 40)
ax2.set_ylim(0, 4.8)
ax2.grid(True, linestyle='--', alpha=0.5)
ax2.legend(loc='lower right', fontsize=8)

# Panel 3: Evolución de Capital Grossman-Zhou ($1,000 inicial)
ax3 = axes[1, 0]
hist_gz_brasil = results["lottobrasil"]["sim"]["history_gz"]
hist_gz_bicho = results["lottobicho"]["sim"]["history_gz"]

ax3.plot(hist_gz_bicho, label=f"Lotto Bicho (GZ Floor 40%): ${hist_gz_bicho[-1]:,.0f} USD (MDD 27.3%)", color='#ff6f00', linewidth=2)
ax3.plot(hist_gz_brasil, label=f"Lotto Brasil (GZ Floor 40%): ${hist_gz_brasil[-1]:,.0f} USD (MDD 26.9%)", color='#009c3b', linewidth=2)
ax3.axhline(1000, color='black', linestyle='--', label='Capital Inicial ($1,000 USD)')
ax3.set_yscale('log')
ax3.set_title("Crecimiento de Capital con Control de Riesgo (Grossman-Zhou MDD Floor 40%)", fontweight='bold')
ax3.set_xlabel("Número de Señales Ejecutadas (Gatillo Post-Fallo 1)")
ax3.set_ylabel("Balance USD (Escala Logarítmica)")
ax3.grid(True, linestyle='--', alpha=0.5)
ax3.legend(loc='upper left', fontsize=9)

# Panel 4: Comparativa de Métricas Cuantitativas
ax4 = axes[1, 1]
categories = ['Supresión L1-6 (Z)', 'Pico Máx Lag 12 (%)', 'Win Rate Canasta (%)', 'ROI Plano (%)', 'Control MDD GZ (%)']
brasil_vals = [
    abs(df_b.loc[df_b["lag"]<=6, "z_score"].mean()),
    df_b.loc[df_b["lag"]==12, "pct_filt"].values[0],
    results["lottobrasil"]["portal_bt"]["win_rate"],
    results["lottobrasil"]["portal_bt"]["roi"],
    results["lottobrasil"]["sim"]["mdd_gz"]
]
bicho_vals = [
    abs(df_bi.loc[df_bi["lag"]<=6, "z_score"].mean()),
    df_bi.loc[df_bi["lag"]==12, "pct_filt"].values[0],
    results["lottobicho"]["portal_bt"]["win_rate"],
    results["lottobicho"]["portal_bt"]["roi"],
    results["lottobicho"]["sim"]["mdd_gz"]
]

x = np.arange(len(categories))
width = 0.35

rects1 = ax4.bar(x - width/2, brasil_vals, width, label='Lotto Brasil (37x)', color='#009c3b', alpha=0.85)
rects2 = ax4.bar(x + width/2, bicho_vals, width, label='Lotto Bicho (35x)', color='#ff6f00', alpha=0.85)

for rect in rects1:
    h = rect.get_height()
    ax4.annotate(f'{h:.1f}', xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold')

for rect in rects2:
    h = rect.get_height()
    ax4.annotate(f'{h:.1f}', xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold')

ax4.set_title("Resumen Comparativo de Métricas Clave", fontweight='bold')
ax4.set_xticks(x)
ax4.set_xticklabels(categories, fontsize=9)
ax4.set_ylabel("Valor de Métrica")
ax4.grid(True, axis='y', linestyle='--', alpha=0.5)
ax4.legend(loc='upper right', fontsize=9)

plt.tight_layout()
plt.subplots_adjust(top=0.91)
plt.savefig(OUTPUT_PNG, dpi=200)
print(f"Gráfica guardada exitosamente en: {OUTPUT_PNG}")
