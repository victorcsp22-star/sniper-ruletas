"""
========================================================================================
 MOTOR INSTITUCIONAL DE BACKTEST SEMANAL CON INTERÉS COMPUESTO (7 RULETAS)
========================================================================================
Ejecuta la simulación cronológica estricta con capital inicial de $200.00 USD:
 - Modelo: Step-Compounding Semanal (0.75x Kelly Fijo reiniciado cada 7 días).
 - Cartera Oficial: 7 Ruletas (Núcleo Venezuela + Nuevas Ruletas Validadas).
 - Causalidad Temporal Estricta: Sin fuga de futuro (No Look-Ahead).
 - Conciliación Contable Exacta al Centavo: Sum(PnL) == Balance Final - Balance Inicial.
========================================================================================
"""

import os
import sys
import datetime
import numpy as np
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(r"C:\Users\victo\nuevas_ruletas")
from config import RULETAS_CONFIG, DEFAULT_BANKROLL, MIN_BET, MDD_FLOOR, WEEKLY_KELLY_MULTIPLIER

CONFIG_7 = {k: v for k, v in RULETAS_CONFIG.items() if v.get("active", True)}


def run_institutional_weekly_backtest(initial_bankroll: float = 200.0, use_mdd_cushion: bool = False):
    print("=" * 115)
    print(f"🔬 BACKTEST INSTITUCIONAL SEMANAL | CAPITAL INICIAL: ${initial_bankroll:,.2f} USD")
    print(f"   Modelo: Step-Compounding 7 Días (0.75x Kelly) | Protección MDD Cushion: {use_mdd_cushion}")
    print("=" * 115)

    # 1. Extracción de eventos cronológicos ordenados
    all_events = []
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
        target_streaks = cfg.get("target_streaks", [1])
        nums = df["numero"].tolist()
        min_idx = max(lags) + 6

        streak = 0
        for i in range(min_idx, len(nums)):
            actual = nums[i]
            rec6 = set(nums[i-6:i])
            cands = list(set([nums[i-l] for l in lags]) - rec6)
            if cands:
                hit = (actual in cands)
                if streak in target_streaks:
                    all_events.append({
                        "dt": df.iloc[i]["sort_dt"],
                        "fecha": df.iloc[i]["fecha"],
                        "hora": df.iloc[i]["hora"],
                        "ruleta": r_name,
                        "actual": actual,
                        "cands": cands,
                        "cost_units": len(cands),
                        "hit": hit,
                        "payout": payout,
                        "f_unit": f_unit,
                        "streak": streak
                    })
                streak = 0 if hit else streak + 1

    all_events.sort(key=lambda x: x["dt"])
    total_events = len(all_events)
    print(f"✅ Total Disparos Tácticos Registrados: {total_events:,}")

    # 2. Agrupación por Ciclos Semanales de 7 Días
    start_dt = all_events[0]["dt"]
    for ev in all_events:
        ev["week_idx"] = int((ev["dt"] - start_dt).total_seconds() // (7 * 86400))

    total_weeks = all_events[-1]["week_idx"] + 1
    weeks_dict = {w: [] for w in range(total_weeks)}
    for ev in all_events:
        weeks_dict[ev["week_idx"]].append(ev)

    # 3. Simulación de Interés Compuesto Semanal
    bankroll = initial_bankroll
    peak_bankroll = bankroll
    max_drawdown = 0.0

    weekly_summary = []
    total_invested_cash = 0.0
    total_collected_cash = 0.0
    total_wins = 0
    total_losses = 0

    running_reconciled_pnl = 0.0

    for w_idx in range(total_weeks):
        events_this_week = weeks_dict[w_idx]
        b_start_week = bankroll

        # Cálculo de colchón Grossman-Zhou si está activo
        if use_mdd_cushion:
            floor = (1.0 - MDD_FLOOR) * peak_bankroll
            cushion = max(0.0, b_start_week - floor)
            gz_mult = min(1.0, max(0.0, cushion / (MDD_FLOOR * peak_bankroll))) if (MDD_FLOOR * peak_bankroll) > 0 else 1.0
        else:
            gz_mult = 1.0

        # Apuestas fijas calculadas al inicio de la semana
        weekly_stakes = {}
        for r_name, cfg in CONFIG_7.items():
            base_stk = b_start_week * cfg["f_unit"] * WEEKLY_KELLY_MULTIPLIER * gz_mult
            weekly_stakes[r_name] = max(MIN_BET, round(base_stk, 2))

        week_pnl = 0.0
        week_inv = 0.0
        week_cob = 0.0
        week_wins = 0
        week_losses = 0

        for ev in events_this_week:
            r = ev["ruleta"]
            stk = weekly_stakes[r]
            cost = round(stk * ev["cost_units"], 2)
            cob = round(stk * ev["payout"], 2) if ev["hit"] else 0.0
            pnl = round(cob - cost, 2)

            week_inv += cost
            week_cob += cob
            week_pnl += pnl
            running_reconciled_pnl += pnl

            if ev["hit"]:
                week_wins += 1
                total_wins += 1
            else:
                week_losses += 1
                total_losses += 1

            total_invested_cash += cost
            total_collected_cash += cob

            # Seguimiento intradía del drawdown
            curr_intra_b = bankroll + (week_pnl)
            if curr_intra_b > peak_bankroll:
                peak_bankroll = curr_intra_b
            dd = (peak_bankroll - curr_intra_b) / peak_bankroll if peak_bankroll > 0 else 0.0
            if dd > max_drawdown:
                max_drawdown = dd

        b_end_week = round(b_start_week + week_pnl, 2)
        bankroll = max(10.0, b_end_week) # Piso de insolvencia

        ret_pct = (week_pnl / b_start_week * 100.0) if b_start_week > 0 else 0.0
        date_start_str = events_this_week[0]["fecha"] if events_this_week else "---"
        date_end_str = events_this_week[-1]["fecha"] if events_this_week else "---"

        weekly_summary.append({
            "week": w_idx + 1,
            "date_range": f"{date_start_str} al {date_end_str}",
            "disparos": len(events_this_week),
            "aciertos": week_wins,
            "fallos": week_losses,
            "win_rate": (week_wins / len(events_this_week) * 100.0) if events_this_week else 0.0,
            "b_inicio": b_start_week,
            "b_final": b_end_week,
            "pnl": week_pnl,
            "ret_pct": ret_pct,
            "peak": peak_bankroll
        })

    # Conciliación matemática exacta
    net_growth = round(bankroll - initial_bankroll, 2)
    discrepancy = abs(net_growth - round(running_reconciled_pnl, 2))

    df_weeks = pd.DataFrame(weekly_summary)
    pos_weeks = len(df_weeks[df_weeks["pnl"] > 0])
    neg_weeks = len(df_weeks[df_weeks["pnl"] < 0])
    zero_weeks = len(df_weeks[df_weeks["pnl"] == 0])

    print("\n" + "=" * 115)
    print(" 📊 RESULTADOS CONSOLIDADOS DEL BACKTEST INSTITUCIONAL")
    print("=" * 115)
    print(f"  • Capital Inicial                    : ${initial_bankroll:,.2f} USD")
    print(f"  • Capital Final Auditado             : ${bankroll:,.2f} USD")
    print(f"  • Ganancia Neta Limpia (PnL)         : +${net_growth:,.2f} USD")
    print(f"  • Multiplicador de Capital Total     : {bankroll / initial_bankroll:,.2f}x")
    print(f"  • Discrepancia Contable al Centavo   : ${discrepancy:.6f} USD (0.00 = Conciliación Perfecta)")
    print(f"  • Período Histórico Evaluado         : {total_weeks} Semanas ({all_events[0]['fecha']} a {all_events[-1]['fecha']})")
    print(f"  • Total de Disparos Realizados       : {total_events:,}")
    print(f"  • Disparos Acertados (Wins)          : {total_wins:,} ({total_wins / total_events * 100:.2f}%)")
    print(f"  • Disparos Fallados (Losses)         : {total_losses:,} ({total_losses / total_events * 100:.2f}%)")
    print(f"  • Dinero Total Invertido             : ${total_invested_cash:,.2f} USD")
    print(f"  • Dinero Total Cobrado (Premios)     : ${total_collected_cash:,.2f} USD")
    print(f"  • ROI de Fichas (Flat-Betting)       : +{(sum(e['payout'] for e in all_events if e['hit']) - sum(e['cost_units'] for e in all_events)) / sum(e['cost_units'] for e in all_events) * 100:.2f}%")
    print(f"  • Semanas Ganadoras                  : {pos_weeks} de {total_weeks} ({pos_weeks / total_weeks * 100:.1f}%)")
    print(f"  • Semanas Perdedoras                 : {neg_weeks} de {total_weeks} ({neg_weeks / total_weeks * 100:.1f}%)")
    print(f"  • Retorno Semanal Promedio           : {df_weeks['ret_pct'].mean():+.2f}%")
    print(f"  • Desviación Estándar Semanal        : {df_weeks['ret_pct'].std():.2f}%")
    print(f"  • Ratio de Sharpe Semanal Anualizado : {(df_weeks['ret_pct'].mean() / df_weeks['ret_pct'].std() * np.sqrt(52)):.2f}")
    downside_std = df_weeks[df_weeks['ret_pct'] < 0]['ret_pct'].std()
    sortino = (df_weeks['ret_pct'].mean() / downside_std * np.sqrt(52)) if downside_std > 0 else 0.0
    print(f"  • Ratio de Sortino Anualizado        : {sortino:.2f}")
    print(f"  • Pico Máximo Registrado (ATH)       : ${peak_bankroll:,.2f} USD")
    print(f"  • Máximo Drawdown Histórico          : {max_drawdown * 100:.2f}%")
    print("=" * 115 + "\n")

    # Muestra de las últimas 10 semanas
    print("📅 DESGLOSE DE LAS ÚLTIMAS 10 SEMANAS:")
    print("-" * 115)
    cols_display = ["week", "date_range", "disparos", "aciertos", "win_rate", "b_inicio", "pnl", "ret_pct", "b_final"]
    df_recent = df_weeks.tail(10)[cols_display].copy()
    for _, row in df_recent.iterrows():
        pnl_s = f"{'+' if row['pnl']>=0 else ''}${row['pnl']:,.2f}"
        ret_s = f"{'+' if row['ret_pct']>=0 else ''}{row['ret_pct']:.2f}%"
        print(f" Semana {int(row['week']):>3} ({row['date_range']}) | Disparos: {int(row['disparos']):>2} (Wins: {int(row['aciertos']):>2}) | Base: ${row['b_inicio']:>10,.2f} | PnL: {pnl_s:>12} ({ret_s:>8}) | Cierre: ${row['b_final']:>10,.2f}")
    print("-" * 115 + "\n")

    return {
        "final_bankroll": bankroll,
        "net_growth": net_growth,
        "max_drawdown": max_drawdown,
        "total_weeks": total_weeks,
        "pos_weeks": pos_weeks,
        "total_events": total_events,
        "total_wins": total_wins,
        "win_rate": total_wins / total_events * 100.0,
        "df_weeks": df_weeks
    }


if __name__ == "__main__":
    # 1. Backtest Oficial: Step-Compounding Semanal 0.75x Kelly
    print(">>> EJECUTANDO MODELO 1: Step-Compounding Semanal 0.75x Kelly Estándar")
    run_institutional_weekly_backtest(initial_bankroll=200.0, use_mdd_cushion=False)

    # 2. Backtest Defensivo: Step-Compounding con Colchón Grossman-Zhou
    print("\n>>> EJECUTANDO MODELO 2: Step-Compounding Semanal con Colchón Grossman-Zhou (MDD Floor 40%)")
    run_institutional_weekly_backtest(initial_bankroll=200.0, use_mdd_cushion=True)
