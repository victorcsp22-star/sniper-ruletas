"""
========================================================================================
 GENERADOR DE GRÁFICA: CARTERA SIN BRASIL (8 RULETAS: VZLA + NUEVAS)
========================================================================================
Genera la curva de equidad acumulada y drawdown para la cartera de 8 ruletas
excluyendo Brasil, comparando el gatillo uniforme vs gatillo afinado por ruleta.
========================================================================================
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from compare_triggers_and_portfolio_no_brasil import simulate_portfolio

OUTPUT_DIR = r"C:\Users\victo\nuevas_ruletas"
ARTIFACT_DIR = r"C:\Users\victo\.gemini\antigravity\brain\b416ad84-eb18-4af1-a597-d96da11175e8"

def generate_plot():
    res_uni = simulate_portfolio(mode="uniform")
    res_tune = simulate_portfolio(mode="tuned")

    df_uni = pd.DataFrame(res_uni["events"])
    df_uni["date"] = pd.to_datetime(df_uni["dt"]).dt.date
    daily_uni = df_uni.groupby("date")["pnl"].sum().reset_index()
    daily_uni["cum_pnl"] = daily_uni["pnl"].cumsum()

    df_tune = pd.DataFrame(res_tune["events"])
    df_tune["date"] = pd.to_datetime(df_tune["dt"]).dt.date
    daily_tune = df_tune.groupby("date")["pnl"].sum().reset_index()
    daily_tune["cum_pnl"] = daily_tune["pnl"].cumsum()

    # Combinar en un solo DataFrame por fecha
    merged = pd.merge(daily_uni[["date", "cum_pnl"]], daily_tune[["date", "cum_pnl"]], on="date", how="outer", suffixes=("_uni", "_tune"))
    merged["date"] = pd.to_datetime(merged["date"])
    merged = merged.sort_values(by="date").ffill().fillna(0.0)

    # Drawdown del afinado
    peak_tune = merged["cum_pnl_tune"].cummax()
    dd_tune = peak_tune - merged["cum_pnl_tune"]

    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), gridspec_kw={'height_ratios': [2.2, 1]}, sharex=True)

    # Subplot 1: Curva de Equidad
    ax1.plot(merged["date"], merged["cum_pnl_tune"], label=f"Gatillo Afinado por Ruleta (+${res_tune['pnl']:,.2f} USD | ROI: {res_tune['roi']:+.1f}%)", color="#1b5e20", linewidth=3.2, zorder=5)
    ax1.plot(merged["date"], merged["cum_pnl_uni"], label=f"Gatillo Uniforme Racha 1 (+${res_uni['pnl']:,.2f} USD | ROI: {res_uni['roi']:+.1f}%)", color="#0277bd", linewidth=2.0, linestyle="--", alpha=0.85)

    ax1.axhline(0, color="black", linestyle="--", linewidth=1.0, alpha=0.6)
    ax1.set_title("Desempeno Cuantitativo: Cartera Sin Brasil (8 Ruletas: Venezuela 5 + Nuevas 3)\nComparativa: Gatillo Uniforme Racha 1 vs Gatillo Afinado por Perfil Empirico ($1 Fijo)", fontsize=13, fontweight="bold", pad=12)
    ax1.set_ylabel("Beneficio Acumulado Neto (USD)", fontsize=11, fontweight="bold")
    ax1.legend(loc="upper left", frameon=True, framealpha=0.9, facecolor="white", edgecolor="#cccccc", fontsize=10)
    ax1.grid(True, linestyle=":", alpha=0.6)

    # Subplot 2: Drawdown
    ax2.fill_between(merged["date"], 0, -dd_tune, color="#c62828", alpha=0.45, label=f"Drawdown Agregado Afinado (Max DD: -${dd_tune.max():,.2f} USD)")
    ax2.plot(merged["date"], -dd_tune, color="#b71c1c", linewidth=1.2)
    ax2.set_title("Curva de Drawdown Historico Agregado (Cartera 8 Ruletas Sin Brasil)", fontsize=11, fontweight="bold", pad=8)
    ax2.set_ylabel("Drawdown (USD)", fontsize=10, fontweight="bold")
    ax2.set_xlabel("Fecha", fontsize=11, fontweight="bold")
    ax2.legend(loc="lower left", frameon=True, framealpha=0.9, facecolor="white", edgecolor="#cccccc", fontsize=10)
    ax2.grid(True, linestyle=":", alpha=0.6)

    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    fig.autofmt_xdate()

    plt.tight_layout()

    out1 = os.path.join(OUTPUT_DIR, "grafica_cartera_sin_brasil.png")
    out2 = os.path.join(ARTIFACT_DIR, "grafica_cartera_sin_brasil.png")

    plt.savefig(out1, dpi=300)
    try:
        os.makedirs(ARTIFACT_DIR, exist_ok=True)
        plt.savefig(out2, dpi=300)
    except Exception:
        pass
    plt.close()
    print("✅ Gráfica sin Brasil guardada correctamente.")

if __name__ == "__main__":
    generate_plot()
