"""
========================================================================================
 BACKTEST FULL KELLY DE LA CARTERA OFICIAL DE 7 RULETAS (CAPITAL INICIAL: $200 USD)
========================================================================================
Simula cronológicamente la cartera de 7 ruletas activas (Lotto Activo, Granjita, Royal,
Guácharo Activo, Gatazo, Mega Animal 40, Monje Millonario) comenzando con $200.00 USD.

Aplica los parámetros del bot de producción:
 - Lags exactos de rebote.
 - Filtro de recencia de 6 horas.
 - Gatillo Sniper (Racha 1 para todas; Racha 1 y 2 para Gatazo).
 - Fracciones unitarias de Kelly (f_unit) por animalito.

Modelos evaluados:
 1. Full Kelly Puro ($200 USD inicial)
 2. Grossman-Zhou (MDD Floor 40% - Preservación de Capital)
 3. Half-Kelly Conservador (0.5x f*)
 4. Flat Staking ($1.00 USD Fijo de Referencia)
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

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

VZ_DIR = r"C:\Users\victo\.gemini\antigravity\scratch\lotto_activo_bot"
NEW_DIR = r"C:\Users\victo\nuevas_ruletas"
ARTIFACT_DIR = r"C:\Users\victo\.gemini\antigravity\brain\b416ad84-eb18-4af1-a597-d96da11175e8"

CONFIG_7 = {
    "Lotto Activo": {
        "file": os.path.join(VZ_DIR, "lotto_activo_2anios.csv"),
        "lags": [20, 18, 14],
        "payout": 30.0,
        "f_unit": 0.00900,  # 0.900% por animalito
        "be_rate": 3.33,
        "target_streaks": [1],
        "emoji": "🦁"
    },
    "La Granjita": {
        "file": os.path.join(VZ_DIR, "la_granjita_2anios.csv"),
        "lags": [15, 17],
        "payout": 30.0,
        "f_unit": 0.00484,  # 0.484% por animalito
        "be_rate": 3.33,
        "target_streaks": [1],
        "emoji": "🐸"
    },
    "Ruleta Royal": {
        "file": os.path.join(VZ_DIR, "ruleta_royal_2anios.csv"),
        "lags": [16, 19, 31],
        "payout": 30.0,
        "f_unit": 0.00826,  # 0.826% por animalito
        "be_rate": 3.33,
        "target_streaks": [1],
        "emoji": "👑"
    },
    "Guacharo Activo": {
        "file": os.path.join(VZ_DIR, "guacharo_activo_2anios.csv"),
        "lags": [31, 41, 25, 42, 35],
        "payout": 60.0,
        "f_unit": 0.00680,  # 0.680% por animalito
        "be_rate": 1.67,
        "target_streaks": [1],
        "emoji": "🦇"
    },
    "Gatazo": {
        "file": os.path.join(NEW_DIR, "gatazo.csv"),
        "lags": [35, 22, 20],
        "payout": 60.0,
        "f_unit": 0.00900,  # 0.900% por animalito
        "be_rate": 1.67,
        "target_streaks": [1, 2],
        "emoji": "🐯"
    },
    "Mega Animal 40": {
        "file": os.path.join(NEW_DIR, "mega_animal_40.csv"),
        "lags": [18, 21, 37],
        "payout": 30.0,
        "f_unit": 0.00800,  # 0.800% por animalito
        "be_rate": 3.33,
        "target_streaks": [1],
        "emoji": "🦏"
    },
    "Monje Millonario": {
        "file": os.path.join(NEW_DIR, "monje_millonario.csv"),
        "lags": [24, 35, 37],
        "payout": 60.0,
        "f_unit": 0.00700,  # 0.700% por animalito
        "be_rate": 1.67,
        "target_streaks": [1],
        "emoji": "🧘‍♂️"
    }
}

def run_kelly_backtest(initial_bankroll=200.0, min_bet=0.10):
    all_draw_events = []

    # 1. Extraer todos los eventos de disparo de cada ruleta con su timestamp
    for r_name, cfg in CONFIG_7.items():
        if not os.path.exists(cfg["file"]):
            print(f"⚠️ Archivo no encontrado: {cfg['file']}")
            continue

        df = pd.read_csv(cfg["file"], dtype={"numero": str})
        df["numero"] = df["numero"].astype(str).str.strip()
        df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        df = df.sort_values(by="sort_dt").reset_index(drop=True)

        lags = cfg["lags"]
        payout = cfg["payout"]
        f_unit = cfg["f_unit"]
        target_streaks = cfg["target_streaks"]
        nums = df["numero"].tolist()
        min_idx = max(lags) + 6

        streak = 0
        for i in range(min_idx, len(nums)):
            actual = nums[i]
            rec6 = set(nums[i-6:i])
            cands = list({nums[i-l] for l in lags} - rec6)

            if cands:
                cost_units = len(cands)
                hit = (actual in cands)

                if streak in target_streaks:
                    all_draw_events.append({
                        "dt": df.iloc[i]["sort_dt"],
                        "fecha": df.iloc[i]["fecha"],
                        "hora": df.iloc[i]["hora"],
                        "ruleta": r_name,
                        "emoji": cfg["emoji"],
                        "cost_units": cost_units,
                        "hit": hit,
                        "payout": payout,
                        "f_unit": f_unit
                    })

                if hit:
                    streak = 0
                else:
                    streak += 1

    # Ordenar cronológicamente todos los sorteos de la cartera unificada
    all_draw_events.sort(key=lambda x: x["dt"])

    # Modelos a evaluar
    models = {
        "full_kelly": {
            "name": "Full Kelly Puro",
            "bankroll": initial_bankroll,
            "peak": initial_bankroll,
            "history": [initial_bankroll],
            "dates": [all_draw_events[0]["dt"]],
            "mdd": 0.0,
            "total_invested": 0.0,
            "total_collected": 0.0,
            "wins": 0,
            "losses": 0
        },
        "grossman_zhou": {
            "name": "Grossman-Zhou (Floor 40%)",
            "bankroll": initial_bankroll,
            "peak": initial_bankroll,
            "history": [initial_bankroll],
            "dates": [all_draw_events[0]["dt"]],
            "mdd": 0.0,
            "total_invested": 0.0,
            "total_collected": 0.0,
            "wins": 0,
            "losses": 0
        },
        "half_kelly": {
            "name": "Half Kelly (0.5x f*)",
            "bankroll": initial_bankroll,
            "peak": initial_bankroll,
            "history": [initial_bankroll],
            "dates": [all_draw_events[0]["dt"]],
            "mdd": 0.0,
            "total_invested": 0.0,
            "total_collected": 0.0,
            "wins": 0,
            "losses": 0
        },
        "flat_1usd": {
            "name": "Apuesta Fija ($1.00 USD Fijo)",
            "bankroll": initial_bankroll,
            "peak": initial_bankroll,
            "history": [initial_bankroll],
            "dates": [all_draw_events[0]["dt"]],
            "mdd": 0.0,
            "total_invested": 0.0,
            "total_collected": 0.0,
            "wins": 0,
            "losses": 0
        }
    }

    # Tracking de rendimiento mensual
    monthly_data = {}

    for ev in all_draw_events:
        dt = ev["dt"]
        month_str = ev["fecha"][:7]
        if month_str not in monthly_data:
            monthly_data[month_str] = {
                "events": 0,
                "hits": 0,
                "start_b": {m: models[m]["bankroll"] for m in models}
            }
        monthly_data[month_str]["events"] += 1
        if ev["hit"]:
            monthly_data[month_str]["hits"] += 1

        cost_units = ev["cost_units"]
        hit = ev["hit"]
        payout = ev["payout"]
        f_unit = ev["f_unit"]

        # 1. Full Kelly Puro
        b_fk = models["full_kelly"]["bankroll"]
        stake_unit_fk = max(min_bet, b_fk * f_unit)
        total_stake_fk = stake_unit_fk * cost_units
        if hit:
            cob_fk = stake_unit_fk * payout
            pnl_fk = cob_fk - total_stake_fk
            models["full_kelly"]["wins"] += 1
        else:
            cob_fk = 0.0
            pnl_fk = -total_stake_fk
            models["full_kelly"]["losses"] += 1
        models["full_kelly"]["bankroll"] = max(1.0, b_fk + pnl_fk)
        models["full_kelly"]["total_invested"] += total_stake_fk
        models["full_kelly"]["total_collected"] += cob_fk
        if models["full_kelly"]["bankroll"] > models["full_kelly"]["peak"]:
            models["full_kelly"]["peak"] = models["full_kelly"]["bankroll"]
        dd_fk = (models["full_kelly"]["peak"] - models["full_kelly"]["bankroll"]) / models["full_kelly"]["peak"]
        models["full_kelly"]["mdd"] = max(models["full_kelly"]["mdd"], dd_fk)
        models["full_kelly"]["history"].append(models["full_kelly"]["bankroll"])
        models["full_kelly"]["dates"].append(dt)

        # 2. Grossman-Zhou (Floor 40%)
        b_gz = models["grossman_zhou"]["bankroll"]
        peak_gz = models["grossman_zhou"]["peak"]
        floor_gz = 0.60 * peak_gz
        cushion_gz = max(0.0, (b_gz - floor_gz) / b_gz) if b_gz > 0 else 0.0
        damping_gz = cushion_gz ** 1.5
        stake_unit_gz = max(min_bet, b_gz * f_unit * damping_gz)
        total_stake_gz = stake_unit_gz * cost_units
        if hit:
            cob_gz = stake_unit_gz * payout
            pnl_gz = cob_gz - total_stake_gz
            models["grossman_zhou"]["wins"] += 1
        else:
            cob_gz = 0.0
            pnl_gz = -total_stake_gz
            models["grossman_zhou"]["losses"] += 1
        models["grossman_zhou"]["bankroll"] = max(1.0, b_gz + pnl_gz)
        models["grossman_zhou"]["total_invested"] += total_stake_gz
        models["grossman_zhou"]["total_collected"] += cob_gz
        if models["grossman_zhou"]["bankroll"] > models["grossman_zhou"]["peak"]:
            models["grossman_zhou"]["peak"] = models["grossman_zhou"]["bankroll"]
        dd_gz = (models["grossman_zhou"]["peak"] - models["grossman_zhou"]["bankroll"]) / models["grossman_zhou"]["peak"]
        models["grossman_zhou"]["mdd"] = max(models["grossman_zhou"]["mdd"], dd_gz)
        models["grossman_zhou"]["history"].append(models["grossman_zhou"]["bankroll"])
        models["grossman_zhou"]["dates"].append(dt)

        # 3. Half-Kelly (0.5x f*)
        b_hk = models["half_kelly"]["bankroll"]
        stake_unit_hk = max(min_bet, b_hk * (f_unit * 0.5))
        total_stake_hk = stake_unit_hk * cost_units
        if hit:
            cob_hk = stake_unit_hk * payout
            pnl_hk = cob_hk - total_stake_hk
            models["half_kelly"]["wins"] += 1
        else:
            cob_hk = 0.0
            pnl_hk = -total_stake_hk
            models["half_kelly"]["losses"] += 1
        models["half_kelly"]["bankroll"] = max(1.0, b_hk + pnl_hk)
        models["half_kelly"]["total_invested"] += total_stake_hk
        models["half_kelly"]["total_collected"] += cob_hk
        if models["half_kelly"]["bankroll"] > models["half_kelly"]["peak"]:
            models["half_kelly"]["peak"] = models["half_kelly"]["bankroll"]
        dd_hk = (models["half_kelly"]["peak"] - models["half_kelly"]["bankroll"]) / models["half_kelly"]["peak"]
        models["half_kelly"]["mdd"] = max(models["half_kelly"]["mdd"], dd_hk)
        models["half_kelly"]["history"].append(models["half_kelly"]["bankroll"])
        models["half_kelly"]["dates"].append(dt)

        # 4. Flat Staking ($1.00 Fijo)
        b_fl = models["flat_1usd"]["bankroll"]
        stake_unit_fl = 1.0
        total_stake_fl = stake_unit_fl * cost_units
        if hit:
            cob_fl = stake_unit_fl * payout
            pnl_fl = cob_fl - total_stake_fl
            models["flat_1usd"]["wins"] += 1
        else:
            cob_fl = 0.0
            pnl_fl = -total_stake_fl
            models["flat_1usd"]["losses"] += 1
        models["flat_1usd"]["bankroll"] = max(1.0, b_fl + pnl_fl)
        models["flat_1usd"]["total_invested"] += total_stake_fl
        models["flat_1usd"]["total_collected"] += cob_fl
        if models["flat_1usd"]["bankroll"] > models["flat_1usd"]["peak"]:
            models["flat_1usd"]["peak"] = models["flat_1usd"]["bankroll"]
        dd_fl = (models["flat_1usd"]["peak"] - models["flat_1usd"]["bankroll"]) / models["flat_1usd"]["peak"]
        models["flat_1usd"]["mdd"] = max(models["flat_1usd"]["mdd"], dd_fl)
        models["flat_1usd"]["history"].append(models["flat_1usd"]["bankroll"])
        models["flat_1usd"]["dates"].append(dt)

    return models, all_draw_events, monthly_data

def generate_kelly_plots(models):
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), gridspec_kw={'height_ratios': [2.2, 1]}, sharex=True)

    dates = models["full_kelly"]["dates"]
    fk_hist = models["full_kelly"]["history"]
    gz_hist = models["grossman_zhou"]["history"]
    hk_hist = models["half_kelly"]["history"]
    fl_hist = models["flat_1usd"]["history"]

    ax1.plot(dates, fk_hist, label=f"Full Kelly Puro (${fk_hist[-1]:,.2f} USD | MDD: {models['full_kelly']['mdd']*100:.1f}%)", color="#1b5e20", linewidth=2.8, zorder=5)
    ax1.plot(dates, gz_hist, label=f"Grossman-Zhou Floor 40% (${gz_hist[-1]:,.2f} USD | MDD: {models['grossman_zhou']['mdd']*100:.1f}%)", color="#0277bd", linewidth=2.2, zorder=4)
    ax1.plot(dates, hk_hist, label=f"Half Kelly (${hk_hist[-1]:,.2f} USD | MDD: {models['half_kelly']['mdd']*100:.1f}%)", color="#f57f17", linewidth=2.0, zorder=3)
    ax1.plot(dates, fl_hist, label=f"Apuesta Plana 1.00 USD Fijo (${fl_hist[-1]:,.2f} USD | MDD: {models['flat_1usd']['mdd']*100:.1f}%)", color="#757575", linewidth=1.5, linestyle="--", zorder=2)

    ax1.set_yscale('log')
    ax1.set_title("Crecimiento de Capital con $200 USD Inicial: Cartera Oficial de 7 Ruletas (2024 - 2026)\nComparativa Cuantitativa de Estrategias de Dimensionamiento Kelly (Escala Logaritmica)", fontsize=13, fontweight="bold", pad=12)
    ax1.set_ylabel("Capital Acumulado (USD - Escala Log)", fontsize=11, fontweight="bold")
    ax1.legend(loc="upper left", frameon=True, framealpha=0.9, facecolor="white", edgecolor="#cccccc", fontsize=10)
    ax1.grid(True, linestyle=":", alpha=0.6)

    # Subplot 2: Curva de Drawdown de Full Kelly vs Grossman-Zhou
    peaks_fk = pd.Series(fk_hist).cummax()
    dd_curve_fk = (peaks_fk - pd.Series(fk_hist)) / peaks_fk * 100.0

    peaks_gz = pd.Series(gz_hist).cummax()
    dd_curve_gz = (peaks_gz - pd.Series(gz_hist)) / peaks_gz * 100.0

    ax2.plot(dates, -dd_curve_fk, label=f"Drawdown Full Kelly (Max: {models['full_kelly']['mdd']*100:.1f}%)", color="#b71c1c", linewidth=1.2, alpha=0.7)
    ax2.plot(dates, -dd_curve_gz, label=f"Drawdown Grossman-Zhou (Max: {models['grossman_zhou']['mdd']*100:.1f}%)", color="#0277bd", linewidth=1.5)
    ax2.fill_between(dates, 0, -dd_curve_gz, color="#0277bd", alpha=0.25)
    ax2.set_title("Drawdown Porcentual Comparativo: Full Kelly vs Grossman-Zhou", fontsize=11, fontweight="bold", pad=8)
    ax2.set_ylabel("Drawdown (%)", fontsize=10, fontweight="bold")
    ax2.set_xlabel("Fecha", fontsize=11, fontweight="bold")
    ax2.legend(loc="lower left", frameon=True, framealpha=0.9, facecolor="white", edgecolor="#cccccc", fontsize=10)
    ax2.grid(True, linestyle=":", alpha=0.6)

    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    fig.autofmt_xdate()

    plt.tight_layout()

    out1 = os.path.join(NEW_DIR, "grafica_full_kelly_200usd_7ruletas.png")
    out2 = os.path.join(ARTIFACT_DIR, "grafica_full_kelly_200usd_7ruletas.png")

    plt.savefig(out1, dpi=300)
    try:
        os.makedirs(ARTIFACT_DIR, exist_ok=True)
        plt.savefig(out2, dpi=300)
    except Exception:
        pass
    plt.close()
    print("✅ Gráficas de Kelly generadas exitosamente.")

if __name__ == "__main__":
    models, events, monthly = run_kelly_backtest(initial_bankroll=200.0)

    print("=" * 115)
    print(" 🌟 RESULTADOS DEL BACKTEST CON CAPITAL INICIAL DE $200.00 USD (CARTERA 7 RULETAS)")
    print("=" * 115)
    print(f" {'Modelo de Gestión':<30} | {'Capital Final':<16} | {'Beneficio Neto':<16} | {'Multiplicador':<14} | {'Max Drawdown':<14} | {'Win Rate'}")
    print("-" * 115)

    for m_key, m in models.items():
        pnl = m["bankroll"] - 200.0
        mult = m["bankroll"] / 200.0
        wr = (m["wins"] / (m["wins"] + m["losses"]) * 100.0)
        pnl_str = f"{'+' if pnl>=0 else ''}${pnl:,.2f} USD"
        bank_str = f"${m['bankroll']:,.2f} USD"
        mult_str = f"{mult:,.1f}x"
        mdd_str = f"{m['mdd']*100:.1f}%"
        print(f" {m['name']:<30} | {bank_str:>16} | {pnl_str:>16} | {mult_str:>14} | {mdd_str:>14} | {wr:>6.2f}%")
    print("-" * 115)
    print(" 📅 DESGLOSE MENSUAL DE CAPITAL (INICIO DE MES CON $200 USD INICIAL):")
    print("-" * 115)
    print(f" {'Mes':<8} | {'Disparos':<8} | {'Ganadas':<7} | {'Win Rate':<8} | {'Full Kelly':<16} | {'Grossman-Zhou':<16} | {'Plana $1':<12}")
    print("-" * 115)
    for m_str, d in sorted(monthly.items()):
        wr = d["hits"] / d["events"] * 100.0 if d["events"] > 0 else 0.0
        fk = d["start_b"]["full_kelly"]
        gz = d["start_b"]["grossman_zhou"]
        fl = d["start_b"]["flat_1usd"]
        print(f" {m_str:<8} | {d['events']:>8} | {d['hits']:>7} | {wr:>7.1f}% | ${fk:>14,.2f} | ${gz:>14,.2f} | ${fl:>10,.2f}")
    print("=" * 115 + "\n")

    generate_kelly_plots(models)
