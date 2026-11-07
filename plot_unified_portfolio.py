"""
========================================================================================
 GENERADOR DE GRÁFICAS DE ALTA RESOLUCIÓN: CARTERA UNIFICADA (10 RULETAS)
========================================================================================
Genera curvas de equidad acumulada, análisis de drawdown y desempeño mensual
para los 3 componentes y la cartera total unificada.
========================================================================================
"""

import os
import sys
import datetime
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from backtest_unified_portfolio import PORTFOLIOS, run_simulation

OUTPUT_DIR = r"C:\Users\victo\nuevas_ruletas"
ARTIFACT_DIR = r"C:\Users\victo\.gemini\antigravity\brain\b416ad84-eb18-4af1-a597-d96da11175e8"

def generate_unified_plot():
    print("📊 Calculando simulación cronológica para la gráfica unificada...")
    ruleta_stats, all_events = run_simulation()

    df_events = pd.DataFrame(all_events)
    df_events = df_events.sort_values(by="dt").reset_index(drop=True)
    df_events["date"] = pd.to_datetime(df_events["fecha"])

    # Separar por portafolios
    p_vzla_name = "🇻🇪 Cartera Venezuela (5 Ruletas)"
    p_bras_name = "🇧🇷 Cartera Brasil (2 Ruletas)"
    p_new_name = "🚀 Nuevas Ruletas Confirmadas (3 Ruletas)"

    # Crear series temporales acumuladas diarias
    daily_groups = df_events.groupby(["date", "portfolio"])["pnl"].sum().unstack(fill_value=0.0)

    # Asegurar que todas las columnas existan
    for col in [p_vzla_name, p_bras_name, p_new_name]:
        if col not in daily_groups.columns:
            daily_groups[col] = 0.0

    daily_groups["Total Unificado"] = daily_groups[p_vzla_name] + daily_groups[p_bras_name] + daily_groups[p_new_name]

    cum_df = daily_groups.cumsum()

    # Calcular Drawdown de la cartera total
    peak = cum_df["Total Unificado"].cummax()
    drawdown = peak - cum_df["Total Unificado"]

    # Configurar estilo visual profesional
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), gridspec_kw={'height_ratios': [2.2, 1]}, sharex=True)

    # Subplot 1: Curvas de Equidad Acumulada
    ax1.plot(cum_df.index, cum_df["Total Unificado"], label=f"Total Cartera Unificada (+${cum_df['Total Unificado'].iloc[-1]:,.2f} USD)", color="#1b5e20", linewidth=3.2, zorder=5)
    ax1.plot(cum_df.index, cum_df[p_vzla_name], label=f"Venezuela (5 Ruletas) (+${cum_df[p_vzla_name].iloc[-1]:,.2f} USD)", color="#0d47a1", linewidth=2.0, alpha=0.85)
    ax1.plot(cum_df.index, cum_df[p_bras_name], label=f"Brasil (2 Ruletas) (+${cum_df[p_bras_name].iloc[-1]:,.2f} USD)", color="#f57f17", linewidth=2.0, alpha=0.85)
    ax1.plot(cum_df.index, cum_df[p_new_name], label=f"Nuevas Ruletas (+${cum_df[p_new_name].iloc[-1]:,.2f} USD)", color="#d81b60", linewidth=2.2, alpha=0.95)

    ax1.axhline(0, color="black", linestyle="--", linewidth=1.0, alpha=0.6)
    ax1.set_title("Desempeno Cuantitativo Consolidado: Cartera Unificada (10 Ruletas en Paralelo)\nEstrategia Gatillo Sniper Racha 1 a $1.00 USD Fijo por Animalito (2024 - 2026)", fontsize=13, fontweight="bold", pad=12)
    ax1.set_ylabel("Beneficio Acumulado Neto (USD)", fontsize=11, fontweight="bold")
    ax1.legend(loc="upper left", frameon=True, framealpha=0.9, facecolor="white", edgecolor="#cccccc", fontsize=10)
    ax1.grid(True, linestyle=":", alpha=0.6)

    # Subplot 2: Drawdown Acumulado de la Cartera Total
    ax2.fill_between(drawdown.index, 0, -drawdown, color="#c62828", alpha=0.45, label=f"Drawdown Agregado (Max DD: -${drawdown.max():,.2f} USD)")
    ax2.plot(drawdown.index, -drawdown, color="#b71c1c", linewidth=1.2)
    ax2.set_title("Curva de Drawdown Historico Agregado de la Cartera Total ($1 Fijo)", fontsize=11, fontweight="bold", pad=8)
    ax2.set_ylabel("Drawdown (USD)", fontsize=10, fontweight="bold")
    ax2.set_xlabel("Fecha", fontsize=11, fontweight="bold")
    ax2.legend(loc="lower left", frameon=True, framealpha=0.9, facecolor="white", edgecolor="#cccccc", fontsize=10)
    ax2.grid(True, linestyle=":", alpha=0.6)

    # Formatear eje de fechas
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    fig.autofmt_xdate()

    plt.tight_layout()

    out_file1 = os.path.join(OUTPUT_DIR, "grafica_cartera_unificada.png")
    out_file2 = os.path.join(ARTIFACT_DIR, "grafica_cartera_unificada.png")

    plt.savefig(out_file1, dpi=300)
    print(f"✅ Gráfica guardada en: {out_file1}")

    try:
        os.makedirs(ARTIFACT_DIR, exist_ok=True)
        plt.savefig(out_file2, dpi=300)
        print(f"✅ Gráfica copiada a los artefactos: {out_file2}")
    except Exception as e:
        print(f"⚠️ No se pudo copiar a artefactos: {e}")

    plt.close()

if __name__ == "__main__":
    generate_unified_plot()
