"""
Generación de gráficos de alta fidelidad para el Backtest Minucioso de la Cartera Brasil con $200 USD.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from compare_trigger_modes import simulate_mode

ARTIFACT_DIR = r"C:\Users\victo\.gemini\antigravity\brain\b416ad84-eb18-4af1-a597-d96da11175e8"
OUTPUT_PNG = os.path.join(ARTIFACT_DIR, "grafica_backtest_brasil_200usd.png")

res_single = simulate_mode("single_shot", initial_bankroll=200.0, mdd_floor=0.40)
res_cont = simulate_mode("continuous", initial_bankroll=200.0, mdd_floor=0.40)

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle("BACKTEST MINUCIOSO DE LA CARTERA BRASIL (Lotto Brasil & Lotto Bicho)\nCapital Inicial: $200.00 USD | 2 Años (2024 - 2026) | 8,633 Sorteos Oficiales", 
             fontsize=15, fontweight='bold', y=0.98)

# Panel 1: Modo Continuo (streak >= 1) - Crecimiento Compuesto
ax1 = axes[0, 0]
h_cont_fk = res_cont["history_fk"]
h_cont_gz = res_cont["history_gz"]

ax1.plot(h_cont_fk, label=f"Full Kelly Puro: ${res_cont['final_fk']:,.0f} USD (MDD {res_cont['mdd_fk']:.1f}%)", color='#d50000', linewidth=1.5, alpha=0.8)
ax1.plot(h_cont_gz, label=f"Grossman-Zhou (Floor 40%): ${res_cont['final_gz']:,.2f} USD (MDD {res_cont['mdd_gz']:.1f}%)", color='#00c853', linewidth=2.2)
ax1.axhline(200, color='black', linestyle=':', label='Capital Inicial ($200 USD)')
ax1.set_yscale('log')
ax1.set_title("MODO 1: Disparo Continuo (streak >= 1) [Alta Frecuencia]", fontweight='bold')
ax1.set_xlabel("Número de Apuestas Ejecutadas (~15,170 en 2 años)")
ax1.set_ylabel("Balance USD (Escala Logarítmica)")
ax1.grid(True, linestyle='--', alpha=0.5)
ax1.legend(loc='lower right', fontsize=8)

# Panel 2: Modo Disparo Único Sniper (streak == 1) - Preservación de Capital
ax2 = axes[0, 1]
h_s_fk = res_single["history_fk"]
h_s_gz = res_single["history_gz"]

ax2.plot(h_s_fk, label=f"Full Kelly Puro: ${res_single['final_fk']:,.2f} USD (MDD {res_single['mdd_fk']:.1f}%)", color='#2962ff', linewidth=1.8)
ax2.plot(h_s_gz, label=f"Grossman-Zhou (Floor 40%): ${res_single['final_gz']:,.2f} USD (MDD {res_single['mdd_gz']:.1f}%)", color='#00b0ff', linewidth=2.0)
ax2.axhline(200, color='black', linestyle=':', label='Capital Inicial ($200 USD)')
ax2.set_title("MODO 2: Disparo Único Sniper (streak == 1) [Baja Frecuencia]", fontweight='bold')
ax2.set_xlabel("Número de Apuestas Ejecutadas (~1,614 en 2 años)")
ax2.set_ylabel("Balance USD")
ax2.grid(True, linestyle='--', alpha=0.5)
ax2.legend(loc='upper left', fontsize=8)

# Panel 3: Drawdowns Submarinos Comparativos (Grossman-Zhou vs Full Kelly)
ax3 = axes[1, 0]
peaks_cont_gz = np.maximum.accumulate(np.array(h_cont_gz))
dd_cont_gz = (peaks_cont_gz - np.array(h_cont_gz)) / peaks_cont_gz * 100.0

peaks_single_gz = np.maximum.accumulate(np.array(h_s_gz))
dd_single_gz = (peaks_single_gz - np.array(h_s_gz)) / peaks_single_gz * 100.0

ax3.plot(dd_cont_gz, color='#00c853', label=f'GZ Continuo (Pico DD: {res_cont["mdd_gz"]:.1f}%)', linewidth=1.2)
ax3.plot(dd_single_gz, color='#00b0ff', label=f'GZ Disparo Único (Pico DD: {res_single["mdd_gz"]:.1f}%)', linewidth=1.2)
ax3.axhline(40.0, color='red', linestyle='--', linewidth=1.5, label='Piso de Seguridad Grossman-Zhou (MDD Floor 40%)')
ax3.set_title("Control Riguroso de Riesgo: Drawdowns Submarinos (%)", fontweight='bold')
ax3.set_xlabel("Progreso de Apuestas")
ax3.set_ylabel("Caída desde el Pico ATH (%)")
ax3.set_ylim(-2, 50)
ax3.grid(True, linestyle='--', alpha=0.5)
ax3.legend(loc='upper right', fontsize=8)

# Panel 4: Tabla Resumen de Métricas
ax4 = axes[1, 1]
ax4.axis('tight')
ax4.axis('off')

col_labels = ["Métrica Cuantitativa", "Modo Continuo (Full Kelly)", "Modo Continuo (GZ Floor 40%)", "Modo Único (Full Kelly)", "Modo Único (GZ Floor 40%)"]
table_data = [
    ["Capital Inicial", "$200.00 USD", "$200.00 USD", "$200.00 USD", "$200.00 USD"],
    ["Balance Final", f"${res_cont['final_fk']:,.2f}", f"${res_cont['final_gz']:,.2f}", f"${res_single['final_fk']:,.2f}", f"${res_single['final_gz']:,.2f}"],
    ["Beneficio Neto", f"${res_cont['final_fk']-200:,.2f}", f"${res_cont['final_gz']-200:,.2f}", f"${res_single['final_fk']-200:,.2f}", f"${res_single['final_gz']-200:,.2f}"],
    ["Multiplicador Capital", f"{res_cont['final_fk']/200:,.0f}x", f"{res_cont['final_gz']/200:,.1f}x", f"{res_single['final_fk']/200:,.2f}x", f"{res_single['final_gz']/200:,.2f}x"],
    ["Max Drawdown (MDD)", f"{res_cont['mdd_fk']:.2f}% (Fatal)", f"{res_cont['mdd_gz']:.2f}% (Controlado)", f"{res_single['mdd_fk']:.2f}% (Severo)", f"{res_single['mdd_gz']:.2f}% (Excelente)"],
    ["Total Señales Ejecutadas", f"{sum(res_cont['signals'].values()):,}", f"{sum(res_cont['signals'].values()):,}", f"{sum(res_single['signals'].values()):,}", f"{sum(res_single['signals'].values()):,}"],
    ["Total Aciertos", f"{sum(res_cont['hits'].values()):,}", f"{sum(res_cont['hits'].values()):,}", f"{sum(res_single['hits'].values()):,}", f"{sum(res_single['hits'].values()):,}"],
    ["Win Rate Global", f"{sum(res_cont['hits'].values())/sum(res_cont['signals'].values())*100:.2f}%", f"{sum(res_cont['hits'].values())/sum(res_cont['signals'].values())*100:.2f}%", f"{sum(res_single['hits'].values())/sum(res_single['signals'].values())*100:.2f}%", f"{sum(res_single['hits'].values())/sum(res_single['signals'].values())*100:.2f}%"],
    ["Win Rate Lotto Brasil", f"{res_cont['hits']['Lotto Brasil']/res_cont['signals']['Lotto Brasil']*100:.2f}%", f"{res_cont['hits']['Lotto Brasil']/res_cont['signals']['Lotto Brasil']*100:.2f}%", f"{res_single['hits']['Lotto Brasil']/res_single['signals']['Lotto Brasil']*100:.2f}%", f"{res_single['hits']['Lotto Brasil']/res_single['signals']['Lotto Brasil']*100:.2f}%"],
    ["Win Rate Lotto Bicho", f"{res_cont['hits']['Lotto Bicho']/res_cont['signals']['Lotto Bicho']*100:.2f}%", f"{res_cont['hits']['Lotto Bicho']/res_cont['signals']['Lotto Bicho']*100:.2f}%", f"{res_single['hits']['Lotto Bicho']/res_single['signals']['Lotto Bicho']*100:.2f}%", f"{res_single['hits']['Lotto Bicho']/res_single['signals']['Lotto Bicho']*100:.2f}%"]
]

table = ax4.table(cellText=table_data, colLabels=col_labels, loc='center', cellLoc='center')
table.auto_set_font_size(False)
table.set_fontsize(8)
table.scale(1.15, 1.6)

plt.tight_layout()
plt.subplots_adjust(top=0.91)
plt.savefig(OUTPUT_PNG, dpi=200)
print(f"Gráfica guardada exitosamente en: {OUTPUT_PNG}")
