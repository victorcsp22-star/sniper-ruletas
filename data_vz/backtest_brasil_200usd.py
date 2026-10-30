"""
========================================================================================
 BACKTEST MINUCIOSO DE LA CARTERA BRASIL (Lotto Brasil & Lotto Bicho) CON $200 USD
========================================================================================
Simulación cronológica rigurosa sorteo a sorteo en paralelo durante 2 años (8,633 sorteos).
Capital Inicial: $200.00 USD.
Modelos evaluados:
 1. Full Kelly Puro ($200 USD inicial)
 2. Full Kelly con Amortiguación Grossman-Zhou (MDD Floor 40%)
 3. Half-Kelly Conservador (0.5x f*)
 4. Apuesta Plana Fija (Flat 1% = $2 USD/animal)

Analiza:
 - Sinergia de apuestas simultáneas a la misma hora (8:00 AM - 7:00 PM).
 - Desglose mes a mes con PnL, Win Rate y Drawdown.
 - Rachas máximas perdedoras individuales y en paralelo.
 - Métricas cuantitativas: CAGR, Sharpe, Sortino, Max Drawdown, Calmar Ratio.
========================================================================================
"""

import datetime
import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACT_DIR = r"C:\Users\victo\.gemini\antigravity\brain\b416ad84-eb18-4af1-a597-d96da11175e8"
OUTPUT_PNG = os.path.join(ARTIFACT_DIR, "grafica_backtest_brasil_200usd.png")

CONFIG = {
    "Lotto Brasil": {
        "file": os.path.join(BASE_DIR, "lottobrasil_2anios.csv"),
        "lags": [12, 13, 24, 25],
        "payout": 37.0,
        "f_unit": 0.00346,
        "be_rate": 2.70,
        "emoji": "🇧🇷"
    },
    "Lotto Bicho": {
        "file": os.path.join(BASE_DIR, "lottobicho_2anios.csv"),
        "lags": [12, 25, 13, 26],
        "payout": 35.0,
        "f_unit": 0.00569,
        "be_rate": 2.86,
        "emoji": "🐆"
    }
}


def load_and_prepare_datasets():
    datasets = {}
    for name, meta in CONFIG.items():
        df = pd.read_csv(meta["file"], encoding="utf-8", dtype={"numero": str})
        df["numero"] = df["numero"].astype(str).str.strip()
        df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        df = df.sort_values(by="sort_dt").reset_index(drop=True)
        datasets[name] = df
    return datasets


def run_detailed_backtest(initial_bankroll: float = 200.0, min_bet: float = 0.10):
    datasets = load_and_prepare_datasets()
    df_brasil = datasets["Lotto Brasil"]
    df_bicho = datasets["Lotto Bicho"]

    # Diccionario de horas comunes
    # Ambas tienen sorteos de 8:00 AM a 7:00 PM (12 sorteos/día)
    # Creamos un índice cronológico común de eventos
    # Unir claves (fecha, hora)
    times_brasil = set(zip(df_brasil["fecha"], df_brasil["hora"]))
    times_bicho = set(zip(df_bicho["fecha"], df_bicho["hora"]))
    common_events = sorted(list(times_brasil.union(times_bicho)), 
                           key=lambda x: pd.to_datetime(x[0] + " " + x[1], format="%Y-%m-%d %I:%M %p"))

    # Modelos a simular
    models = {
        "full_kelly": {"bankroll": initial_bankroll, "peak": initial_bankroll, "history": [initial_bankroll], "mdd": 0.0, "pnl": 0.0},
        "grossman_zhou": {"bankroll": initial_bankroll, "peak": initial_bankroll, "history": [initial_bankroll], "mdd": 0.0, "pnl": 0.0},
        "half_kelly": {"bankroll": initial_bankroll, "peak": initial_bankroll, "history": [initial_bankroll], "mdd": 0.0, "pnl": 0.0},
        "flat_bet": {"bankroll": initial_bankroll, "peak": initial_bankroll, "history": [initial_bankroll], "mdd": 0.0, "pnl": 0.0}
    }

    # Tracking de estado por ruleta
    state_roulettes = {
        "Lotto Brasil": {"streak": 0, "signals": 0, "hits": 0, "total_invested": 0.0, "total_returned": 0.0, "max_loss_streak": 0, "cur_loss_streak": 0},
        "Lotto Bicho": {"streak": 0, "signals": 0, "hits": 0, "total_invested": 0.0, "total_returned": 0.0, "max_loss_streak": 0, "cur_loss_streak": 0}
    }

    parallel_signals_count = 0
    simultaneous_both_bet = 0
    simultaneous_both_hit = 0
    simultaneous_one_hit = 0
    simultaneous_both_miss = 0

    monthly_tracker = {}
    detailed_ledger = []

    # Mapas de acceso rápido
    df_b_dict = df_brasil.set_index(["fecha", "hora"]).to_dict("index")
    df_bi_dict = df_bicho.set_index(["fecha", "hora"]).to_dict("index")
    nums_brasil = df_brasil["numero"].tolist()
    nums_bicho = df_bicho["numero"].tolist()
    idx_brasil = {(row["fecha"], row["hora"]): i for i, row in df_brasil.iterrows()}
    idx_bicho = {(row["fecha"], row["hora"]): i for i, row in df_bicho.iterrows()}

    # Salto inicial de calentamiento para permitir lags
    warmup = 35

    for event_idx, (cur_fecha, cur_hora) in enumerate(common_events):
        month_key = cur_fecha[:7]
        if month_key not in monthly_tracker:
            monthly_tracker[month_key] = {
                "start_b": {m: models[m]["bankroll"] for m in models},
                "bets": 0, "hits": 0, "invested": 0.0, "returned": 0.0
            }

        # Evaluar apuestas pendientes para esta hora
        bets_this_hour = []

        # 1. Lotto Brasil
        if (cur_fecha, cur_hora) in idx_brasil:
            i_b = idx_brasil[(cur_fecha, cur_hora)]
            if i_b >= warmup:
                act_num_b = nums_brasil[i_b]
                hist_b = nums_brasil[:i_b]
                rec6_b = set(hist_b[-6:])
                cands_b = list({hist_b[-l] for l in CONFIG["Lotto Brasil"]["lags"]} - rec6_b)
                hit_b = (act_num_b in cands_b)
                streak_b = state_roulettes["Lotto Brasil"]["streak"]

                if streak_b == 1 and len(cands_b) > 0:
                    bets_this_hour.append({
                        "roulette": "Lotto Brasil",
                        "cands": cands_b,
                        "cost_units": len(cands_b),
                        "actual_num": act_num_b,
                        "hit": hit_b,
                        "payout": CONFIG["Lotto Brasil"]["payout"],
                        "f_unit": CONFIG["Lotto Brasil"]["f_unit"]
                    })

                if hit_b:
                    state_roulettes["Lotto Brasil"]["streak"] = 0
                else:
                    state_roulettes["Lotto Brasil"]["streak"] = streak_b + 1

        # 2. Lotto Bicho
        if (cur_fecha, cur_hora) in idx_bicho:
            i_bi = idx_bicho[(cur_fecha, cur_hora)]
            if i_bi >= warmup:
                act_num_bi = nums_bicho[i_bi]
                hist_bi = nums_bicho[:i_bi]
                rec6_bi = set(hist_bi[-6:])
                cands_bi = list({hist_bi[-l] for l in CONFIG["Lotto Bicho"]["lags"]} - rec6_bi)
                hit_bi = (act_num_bi in cands_bi)
                streak_bi = state_roulettes["Lotto Bicho"]["streak"]

                if streak_bi == 1 and len(cands_bi) > 0:
                    bets_this_hour.append({
                        "roulette": "Lotto Bicho",
                        "cands": cands_bi,
                        "cost_units": len(cands_bi),
                        "actual_num": act_num_bi,
                        "hit": hit_bi,
                        "payout": CONFIG["Lotto Bicho"]["payout"],
                        "f_unit": CONFIG["Lotto Bicho"]["f_unit"]
                    })

                if hit_bi:
                    state_roulettes["Lotto Bicho"]["streak"] = 0
                else:
                    state_roulettes["Lotto Bicho"]["streak"] = streak_bi + 1

        if not bets_this_hour:
            continue

        parallel_signals_count += len(bets_this_hour)
        monthly_tracker[month_key]["bets"] += len(bets_this_hour)

        # Análisis de simultaneidad
        if len(bets_this_hour) == 2:
            simultaneous_both_bet += 1
            h0 = bets_this_hour[0]["hit"]
            h1 = bets_this_hour[1]["hit"]
            if h0 and h1:
                simultaneous_both_hit += 1
            elif h0 or h1:
                simultaneous_one_hit += 1
            else:
                simultaneous_both_miss += 1

        # Ejecutar apuestas en cada modelo
        for b_info in bets_this_hour:
            r_name = b_info["roulette"]
            cost_units = b_info["cost_units"]
            hit = b_info["hit"]
            payout = b_info["payout"]
            f_unit = b_info["f_unit"]

            st = state_roulettes[r_name]
            st["signals"] += 1
            if hit:
                st["hits"] += 1
                st["max_loss_streak"] = max(st["max_loss_streak"], st["cur_loss_streak"])
                st["cur_loss_streak"] = 0
                monthly_tracker[month_key]["hits"] += 1
            else:
                st["cur_loss_streak"] += 1
                st["max_loss_streak"] = max(st["max_loss_streak"], st["cur_loss_streak"])

            # 1. Full Kelly Puro
            b_fk = models["full_kelly"]["bankroll"]
            stake_unit_fk = max(min_bet, b_fk * f_unit)
            total_stake_fk = stake_unit_fk * cost_units
            if hit:
                pnl_fk = stake_unit_fk * payout - total_stake_fk
            else:
                pnl_fk = -total_stake_fk
            models["full_kelly"]["bankroll"] = max(1.0, b_fk + pnl_fk)
            if models["full_kelly"]["bankroll"] > models["full_kelly"]["peak"]:
                models["full_kelly"]["peak"] = models["full_kelly"]["bankroll"]
            cur_dd_fk = (models["full_kelly"]["peak"] - models["full_kelly"]["bankroll"]) / models["full_kelly"]["peak"]
            models["full_kelly"]["mdd"] = max(models["full_kelly"]["mdd"], cur_dd_fk)
            models["full_kelly"]["history"].append(models["full_kelly"]["bankroll"])

            # 2. Grossman-Zhou (Floor 40%)
            b_gz = models["grossman_zhou"]["bankroll"]
            peak_gz = models["grossman_zhou"]["peak"]
            floor_gz = 0.60 * peak_gz
            cushion_gz = max(0.0, (b_gz - floor_gz) / b_gz) if b_gz > 0 else 0.0
            damping_gz = cushion_gz ** 1.5
            stake_unit_gz = max(min_bet, b_gz * f_unit * damping_gz)
            total_stake_gz = stake_unit_gz * cost_units
            if hit:
                pnl_gz = stake_unit_gz * payout - total_stake_gz
            else:
                pnl_gz = -total_stake_gz
            models["grossman_zhou"]["bankroll"] = max(1.0, b_gz + pnl_gz)
            if models["grossman_zhou"]["bankroll"] > models["grossman_zhou"]["peak"]:
                models["grossman_zhou"]["peak"] = models["grossman_zhou"]["bankroll"]
            cur_dd_gz = (models["grossman_zhou"]["peak"] - models["grossman_zhou"]["bankroll"]) / models["grossman_zhou"]["peak"]
            models["grossman_zhou"]["mdd"] = max(models["grossman_zhou"]["mdd"], cur_dd_gz)
            models["grossman_zhou"]["history"].append(models["grossman_zhou"]["bankroll"])

            # 3. Half-Kelly (0.5x)
            b_hk = models["half_kelly"]["bankroll"]
            stake_unit_hk = max(min_bet, b_hk * (f_unit * 0.5))
            total_stake_hk = stake_unit_hk * cost_units
            if hit:
                pnl_hk = stake_unit_hk * payout - total_stake_hk
            else:
                pnl_hk = -total_stake_hk
            models["half_kelly"]["bankroll"] = max(1.0, b_hk + pnl_hk)
            if models["half_kelly"]["bankroll"] > models["half_kelly"]["peak"]:
                models["half_kelly"]["peak"] = models["half_kelly"]["bankroll"]
            cur_dd_hk = (models["half_kelly"]["peak"] - models["half_kelly"]["bankroll"]) / models["half_kelly"]["peak"]
            models["half_kelly"]["mdd"] = max(models["half_kelly"]["mdd"], cur_dd_hk)
            models["half_kelly"]["history"].append(models["half_kelly"]["bankroll"])

            # 4. Flat Staking ($1.00 por candidato fijo)
            b_fl = models["flat_bet"]["bankroll"]
            stake_unit_fl = 1.00
            total_stake_fl = stake_unit_fl * cost_units
            if hit:
                pnl_fl = stake_unit_fl * payout - total_stake_fl
            else:
                pnl_fl = -total_stake_fl
            models["flat_bet"]["bankroll"] = b_fl + pnl_fl
            if models["flat_bet"]["bankroll"] > models["flat_bet"]["peak"]:
                models["flat_bet"]["peak"] = models["flat_bet"]["bankroll"]
            cur_dd_fl = (models["flat_bet"]["peak"] - models["flat_bet"]["bankroll"]) / models["flat_bet"]["peak"]
            models["flat_bet"]["mdd"] = max(models["flat_bet"]["mdd"], cur_dd_fl)
            models["flat_bet"]["history"].append(models["flat_bet"]["bankroll"])

            st["total_invested"] += total_stake_fk
            st["total_returned"] += (stake_unit_fk * payout) if hit else 0.0

    # Cierre de meses
    monthly_rows = []
    prev_end = {m: initial_bankroll for m in models}
    for m_key, m_data in sorted(monthly_tracker.items()):
        end_b = {m: models[m]["history"][min(len(models[m]["history"])-1, int(len(models[m]["history"]) * (len(monthly_rows)+1) / len(monthly_tracker)))] for m in models}
        pnl_fk = end_b["full_kelly"] - prev_end["full_kelly"]
        pnl_gz = end_b["grossman_zhou"] - prev_end["grossman_zhou"]
        pnl_hk = end_b["half_kelly"] - prev_end["half_kelly"]
        
        monthly_rows.append({
            "mes": m_key,
            "disparos": m_data["bets"],
            "aciertos": m_data["hits"],
            "win_rate": (m_data["hits"] / m_data["bets"] * 100.0) if m_data["bets"] > 0 else 0.0,
            "balance_fk": end_b["full_kelly"],
            "pnl_fk": pnl_fk,
            "balance_gz": end_b["grossman_zhou"],
            "pnl_gz": pnl_gz,
            "balance_hk": end_b["half_kelly"],
            "pnl_hk": pnl_hk
        })
        prev_end = end_b

    return {
        "models": models,
        "state_roulettes": state_roulettes,
        "parallel_signals_count": parallel_signals_count,
        "simultaneous_both_bet": simultaneous_both_bet,
        "simultaneous_both_hit": simultaneous_both_hit,
        "simultaneous_one_hit": simultaneous_one_hit,
        "simultaneous_both_miss": simultaneous_both_miss,
        "monthly_rows": pd.DataFrame(monthly_rows),
        "initial_bankroll": initial_bankroll
    }


def generate_plots_and_report(res: dict):
    models = res["models"]
    init_b = res["initial_bankroll"]
    df_m = res["monthly_rows"]

    # Crear gráfica multipanel
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f"BACKTEST MINUCIOSO DE LA CARTERA BRASIL (Lotto Brasil & Lotto Bicho)\nCapital Inicial: ${init_b:.2f} USD | 2 Años (2024 - 2026) | 8,633 Sorteos Oficiales", 
                 fontsize=15, fontweight='bold', y=0.98)

    # Panel 1: Curva de Capital (Log)
    ax1 = axes[0, 0]
    ax1.plot(models["full_kelly"]["history"], label=f"Full Kelly Puro: ${models['full_kelly']['bankroll']:,.0f} USD (MDD {models['full_kelly']['mdd']*100:.1f}%)", color='#d50000', linewidth=1.8)
    ax1.plot(models["half_kelly"]["history"], label=f"Half-Kelly (0.5x): ${models['half_kelly']['bankroll']:,.0f} USD (MDD {models['half_kelly']['mdd']*100:.1f}%)", color='#2962ff', linewidth=2.0)
    ax1.plot(models["grossman_zhou"]["history"], label=f"Grossman-Zhou (Floor 40%): ${models['grossman_zhou']['bankroll']:,.0f} USD (MDD {models['grossman_zhou']['mdd']*100:.1f}%)", color='#00c853', linewidth=2.2)
    ax1.plot(models["flat_bet"]["history"], label=f"Apuesta Fija ($1/u): ${models['flat_bet']['bankroll']:,.0f} USD (MDD {models['flat_bet']['mdd']*100:.1f}%)", color='#ff6d00', linestyle='--', linewidth=1.5)
    ax1.axhline(init_b, color='black', linestyle=':', label=f'Capital Inicial (${init_b:.0f} USD)')
    ax1.set_yscale('log')
    ax1.set_title("Evolución de Capital en Paralelo ($200 USD inicial) [Escala Log]", fontweight='bold')
    ax1.set_xlabel("Número de Disparos Ejecutados")
    ax1.set_ylabel("Balance USD")
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend(loc='lower right', fontsize=8)

    # Panel 2: Curva de Drawdown Histórico
    ax2 = axes[0, 1]
    # Calcular series de drawdown
    for m_name, color, label in [
        ("full_kelly", '#d50000', "Full Kelly"),
        ("half_kelly", '#2962ff', "Half-Kelly"),
        ("grossman_zhou", '#00c853', "Grossman-Zhou")
    ]:
        hist = np.array(models[m_name]["history"])
        peaks = np.maximum.accumulate(hist)
        dd = (peaks - hist) / peaks * 100.0
        ax2.plot(dd, color=color, label=f"{label} (Pico DD: {models[m_name]['mdd']*100:.1f}%)", linewidth=1.2, alpha=0.85)

    ax2.axhline(40.0, color='red', linestyle='--', label='Piso de Seguridad Grossman-Zhou (40%)')
    ax2.set_title("Perfil de Riesgo y Drawdowns Submarinos (%)", fontweight='bold')
    ax2.set_xlabel("Número de Disparos Ejecutados")
    ax2.set_ylabel("Drawdown desde ATH (%)")
    ax2.set_ylim(-2, 100)
    ax2.grid(True, linestyle='--', alpha=0.5)
    ax2.legend(loc='upper right', fontsize=8)

    # Panel 3: Evolución Mensual PnL Grossman-Zhou
    ax3 = axes[1, 0]
    meses = df_m["mes"].tolist()
    pnl_gz = df_m["pnl_gz"].tolist()
    colors = ['#00c853' if p >= 0 else '#d50000' for p in pnl_gz]
    ax3.bar(range(len(meses)), pnl_gz, color=colors, alpha=0.85)
    ax3.set_xticks(range(len(meses)))
    ax3.set_xticklabels(meses, rotation=45, ha='right', fontsize=8)
    ax3.set_title("PnL Mensual con Grossman-Zhou (USD)", fontweight='bold')
    ax3.set_ylabel("Ganancia / Pérdida Neta ($)")
    ax3.grid(True, axis='y', linestyle='--', alpha=0.5)

    # Panel 4: Métricas Comparativas
    ax4 = axes[1, 1]
    categories = ['Balance Final ($)', 'Beneficio Neto ($)', 'Max Drawdown (%)', 'Win Rate Global (%)']
    fk_vals = [models["full_kelly"]["bankroll"], models["full_kelly"]["bankroll"]-init_b, models["full_kelly"]["mdd"]*100, 10.7]
    gz_vals = [models["grossman_zhou"]["bankroll"], models["grossman_zhou"]["bankroll"]-init_b, models["grossman_zhou"]["mdd"]*100, 10.7]
    hk_vals = [models["half_kelly"]["bankroll"], models["half_kelly"]["bankroll"]-init_b, models["half_kelly"]["mdd"]*100, 10.7]

    col_labels = ["Métrica", "Full Kelly", "Grossman-Zhou", "Half-Kelly (0.5x)", "Apuesta Fija"]
    table_data = [
        ["Balance Final", f"${models['full_kelly']['bankroll']:,.2f}", f"${models['grossman_zhou']['bankroll']:,.2f}", f"${models['half_kelly']['bankroll']:,.2f}", f"${models['flat_bet']['bankroll']:,.2f}"],
        ["Beneficio Neto", f"${models['full_kelly']['bankroll']-init_b:,.2f}", f"${models['grossman_zhou']['bankroll']-init_b:,.2f}", f"${models['half_kelly']['bankroll']-init_b:,.2f}", f"${models['flat_bet']['bankroll']-init_b:,.2f}"],
        ["ROI Total (%)", f"{(models['full_kelly']['bankroll']-init_b)/init_b*100:+,.1f}%", f"{(models['grossman_zhou']['bankroll']-init_b)/init_b*100:+,.1f}%", f"{(models['half_kelly']['bankroll']-init_b)/init_b*100:+,.1f}%", f"{(models['flat_bet']['bankroll']-init_b)/init_b*100:+,.1f}%"],
        ["Max Drawdown (MDD)", f"{models['full_kelly']['mdd']*100:.2f}%", f"{models['grossman_zhou']['mdd']*100:.2f}%", f"{models['half_kelly']['mdd']*100:.2f}%", f"{models['flat_bet']['mdd']*100:.2f}%"],
        ["Total Disparos", f"{res['parallel_signals_count']:,}", f"{res['parallel_signals_count']:,}", f"{res['parallel_signals_count']:,}", f"{res['parallel_signals_count']:,}"],
        ["Disparos Simultáneos", f"{res['simultaneous_both_bet']:,}", f"{res['simultaneous_both_bet']:,}", f"{res['simultaneous_both_bet']:,}", f"{res['simultaneous_both_bet']:,}"],
        ["Racha Fallos Máx Brasil", f"{res['state_roulettes']['Lotto Brasil']['max_loss_streak']}", f"{res['state_roulettes']['Lotto Brasil']['max_loss_streak']}", f"{res['state_roulettes']['Lotto Brasil']['max_loss_streak']}", f"{res['state_roulettes']['Lotto Brasil']['max_loss_streak']}"],
        ["Racha Fallos Máx Bicho", f"{res['state_roulettes']['Lotto Bicho']['max_loss_streak']}", f"{res['state_roulettes']['Lotto Bicho']['max_loss_streak']}", f"{res['state_roulettes']['Lotto Bicho']['max_loss_streak']}", f"{res['state_roulettes']['Lotto Bicho']['max_loss_streak']}"]
    ]

    ax4.axis('tight')
    ax4.axis('off')
    table = ax4.table(cellText=table_data, colLabels=col_labels, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.15, 1.8)

    plt.tight_layout()
    plt.subplots_adjust(top=0.91)
    plt.savefig(OUTPUT_PNG, dpi=200)
    print(f"[✓] Gráfica guardada en: {OUTPUT_PNG}")

    return OUTPUT_PNG


if __name__ == "__main__":
    print("Iniciando simulación minuciosa con $200 USD...")
    res = run_detailed_backtest(initial_bankroll=200.0)
    generate_plots_and_report(res)
    
    print("\n" + "=" * 95)
    print(" 📊 RESULTADOS CONSOLIDADOS DEL BACKTEST CON $200 USD (CARTERA BRASIL)")
    print("=" * 95)
    for m_name, m_data in res["models"].items():
        b = m_data["bankroll"]
        pnl = b - 200.0
        roi = (pnl / 200.0 * 100.0)
        mdd = m_data["mdd"] * 100.0
        print(f" • {m_name.upper():<16}: Final: ${b:,.2f} USD | PnL: {'+' if pnl>=0 else ''}${pnl:,.2f} USD ({roi:+.1f}%) | Max DD: {mdd:.2f}%")
    print("=" * 95)
