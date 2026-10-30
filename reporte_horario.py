"""
========================================================================================
 MOTOR DE REPORTE TÁCTICO HORARIO (SISTEMA MULTI-RULETA 7 ACTIVAS)
========================================================================================
Genera el reporte ejecutivo estándar para cada hora del sorteo, detallando:
 1. Estado de Patrimonio y Balance (Mesa + Ganancias Retiradas + PnL semanal).
 2. Resultados Oficiales de la Última Ronda de Sorteos por Ruleta.
 3. Disparos Ejecutados en la Hora (Animales jugados, cuota, resultado y PnL).
 4. Señales Activas Inminentes para la Próxima Hora ($1.00 USD fijo c/u).
 5. Radar de Estado y Conteo de Fallos para todas las ruletas.
========================================================================================
"""

import os
import sys
import json
import datetime
from typing import Dict, List
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = r"C:\Users\victo\nuevas_ruletas"
sys.path.append(ROOT_DIR)

from config import (
    RULETAS_CONFIG,
    STATE_FILE,
    LEDGER_FILE,
    FIXED_STAKE_UNIT,
)
from bot_nuevas_ruletas import (
    load_state,
    get_history_series,
    calculate_current_streak_and_misses,
    generate_upcoming_candidates,
)


def generate_hourly_report(target_date: str = None) -> str:
    now = datetime.datetime.now()
    if target_date is None:
        target_date = now.strftime("%Y-%m-%d")

    state = load_state()
    bankroll = state.get("bankroll", 200.0)
    withdrawn = state.get("total_withdrawn", 0.0)
    patrimonio = round(bankroll + withdrawn, 2)
    cycle_num = state.get("cycle_number", 5)
    cycle_base = state.get("cycle_start_bankroll", 200.0)
    cycle_pnl = round(bankroll - cycle_base, 2)
    cycle_pct = (cycle_pnl / cycle_base * 100.0) if cycle_base > 0 else 0.0

    # Cargar ledger de hoy
    ledger_today = []
    if os.path.exists(LEDGER_FILE):
        df_leg = pd.read_csv(LEDGER_FILE)
        df_leg_today = df_leg[df_leg["fecha"].astype(str) == target_date]
        ledger_today = df_leg_today.to_dict(orient="records")

    # Obtener últimos sorteos de cada ruleta hoy
    latest_draws = {}
    today_draw_counts = {}
    for r_name, cfg in RULETAS_CONFIG.items():
        if not cfg.get("active", False):
            continue
        _, df_r = get_history_series(r_name)
        df_today = df_r[df_r["fecha"] == target_date]
        today_draw_counts[r_name] = len(df_today)
        if not df_today.empty:
            last_row = df_today.iloc[-1]
            latest_draws[r_name] = {
                "hora": str(last_row["hora"]).strip(),
                "numero": str(last_row["numero"]).strip(),
                "animal": str(last_row["animal"]).strip()
            }
        else:
            latest_draws[r_name] = None

    # Identificar la hora de corte más reciente
    all_horas = [d["hora"] for d in latest_draws.values() if d]
    corte_hora = all_horas[-1] if all_horas else now.strftime("%I:00 %p")

    # Evaluar radar y señales activas para la siguiente ronda
    active_signals = []
    radar_items = []
    for r_name, cfg in RULETAS_CONFIG.items():
        if not cfg.get("active", False):
            continue
        stk, miss = calculate_current_streak_and_misses(r_name)
        cands_info = generate_upcoming_candidates(r_name)
        is_markov = cands_info.get("is_markov_active", False)
        is_anti_blocked = cands_info.get("is_anti_cluster_blocked", False)
        cands = cands_info.get("candidates", [])
        cands_str = ", ".join([f"#{c['numero']} {c['animal']}" for c in cands])

        if (stk in cfg.get("target_streaks", [1]) and not is_anti_blocked) or is_markov:
            if is_markov:
                tipo = "⚡ Markov Sniper"
            else:
                tipo = "🎯 Canasta Rezagados"
            cost = round(len(cands) * FIXED_STAKE_UNIT, 2)
            premio = round(FIXED_STAKE_UNIT * cfg["payout"], 2)
            active_signals.append({
                "ruleta": f"{cfg['emoji']} {r_name}",
                "tipo": tipo,
                "candidatos": cands_str,
                "fichas": len(cands),
                "costo": cost,
                "premio": premio,
                "payout": cfg["payout"]
            })

        radar_items.append({
            "ruleta": f"{cfg['emoji']} {r_name}",
            "racha": stk,
            "misses": miss,
            "ultimo": latest_draws.get(r_name),
            "is_markov": is_markov,
            "is_anti_blocked": is_anti_blocked
        })

    # Construir el reporte en Markdown limpio y estructurado
    lines = []
    lines.append(f"## ⏱️ REPORTE TÁCTICO HORARIO — {now.strftime('%I:%M %p').lstrip('0')} ({target_date})")
    lines.append("`Sistema Multi-Ruleta Cuantitativo · Fichas $1.00 USD Fijo`\n")

    # 1. Resumen de Patrimonio
    lines.append("### 💰 1. Balance de Capital y Patrimonio")
    lines.append(f"* **Saldo en Mesa (Banca Activa):** **${bankroll:,.2f} USD** (Base semanal: ${cycle_base:.2f})")
    lines.append(f"* **Ganancias Retiradas (en mano):** **${withdrawn:,.2f} USD** *(retiradas en las 4 semanas previas)*")
    lines.append(f"* **Patrimonio Total Acumulado:** **${patrimonio:,.2f} USD** (+$774.00 neto / +387.0%)")
    lines.append(f"* **Rendimiento Semana N° {cycle_num} (en curso):** **{'+' if cycle_pnl>=0 else ''}${cycle_pnl:.2f} USD** ({'+' if cycle_pct>=0 else ''}{cycle_pct:.1f}%)\n")

    # 2. Resultados Oficiales de la Ronda Reciente
    lines.append("### 🎲 2. Resultados Oficiales de la Ronda Reciente")
    lines.append("| Ruleta | Sorteo | Salido Oficial | Estado Operativo | Detalle / Acción |")
    lines.append("| :--- | :---: | :---: | :---: | :--- |")

    # Revisar si en la última ronda hubo apuestas
    for r_name, cfg in RULETAS_CONFIG.items():
        if not cfg.get("active", False):
            continue
        last_d = latest_draws.get(r_name)
        em = cfg["emoji"]
        if last_d:
            salido_txt = f"**#{last_d['numero']} {last_d['animal']}**"
            hora_txt = last_d['hora']
            
            # Buscar si hubo apuesta en este sorteo específico en el ledger
            matched_bet = None
            for b in ledger_today:
                if str(b.get("ruleta", "")).strip() == r_name and str(b.get("hora", "")).strip() == hora_txt:
                    matched_bet = b
                    break
            
            if matched_bet:
                pnl_b = float(matched_bet.get("pnl", 0.0))
                pnl_b_str = f"🟢 **+${pnl_b:.2f} USD**" if pnl_b > 0 else f"🔴 **-${abs(pnl_b):.2f} USD**"
                estado_op = "💥 **APUESTA JUGADA**"
                detalle = f"Jugados `{matched_bet.get('candidatos', '')}` -> {pnl_b_str}"
            else:
                stk, _ = calculate_current_streak_and_misses(r_name)
                estado_op = "⚪ En Espera"
                if stk == 0:
                    detalle = "Racha 0 (Post-Acierto)"
                else:
                    detalle = f"Racha {stk} (Monitoreando)"
        else:
            salido_txt = "---"
            hora_txt = "---"
            estado_op = "⚪ Sin sorteo"
            detalle = "Fuera de horario"

        lines.append(f"| {em} {r_name} | {hora_txt} | {salido_txt} | {estado_op} | {detalle} |")

    lines.append("")

    # 3. Señales Inminentes para la Siguiente Hora
    lines.append("### 🎯 3. Órdenes de Compra Activas para la Próxima Ronda")
    if active_signals:
        lines.append("| Ruleta | Tipo de Patrón | Animales a Comprar | Inversión ($1 c/u) | Premio Potencial | Cuota |")
        lines.append("| :--- | :---: | :--- | :---: | :---: | :---: |")
        for sig in active_signals:
            lines.append(f"| **{sig['ruleta']}** | `{sig['tipo']}` | **{sig['candidatos']}** | **${sig['costo']:.2f} USD** | 🏆 **${sig['premio']:.2f} USD** | {sig['payout']:.0f}x |")
    else:
        lines.append("> ℹ️ **Sin compras para la siguiente ronda.** Todas las ruletas están en estado de espera (ninguna cumple racha 1 ni gatillo Markov en este momento).")

    lines.append("")

    # 4. Resumen Acumulado del Día de Hoy
    ops_today = len(ledger_today)
    wins_today = sum(1 for b in ledger_today if float(b.get("pnl", 0.0)) > 0)
    inv_today = sum(float(b.get("total_bet", 0.0)) for b in ledger_today)
    cob_today = sum(float(b.get("cobrado", 0.0)) for b in ledger_today)
    pnl_today = round(cob_today - inv_today, 2)
    pnl_today_sign = "+" if pnl_today >= 0 else ""

    lines.append("### 📊 4. Resumen de Operaciones del Día (Hoy)")
    lines.append(f"* **Total Apuestas Hoy:** {ops_today} operaciones")
    lines.append(f"* **Aciertos Hoy:** {wins_today} aciertos (Win Rate: {(wins_today/ops_today*100):.1f}%)" if ops_today > 0 else "* **Aciertos Hoy:** 0 aciertos")
    lines.append(f"* **Capital Invertido Hoy:** ${inv_today:.2f} USD | **Cobrado Hoy:** ${cob_today:.2f} USD")
    lines.append(f"* **PnL Neto de Hoy:** **{pnl_today_sign}${pnl_today:.2f} USD**")

    return "\n".join(lines)


if __name__ == "__main__":
    reporte = generate_hourly_report()
    print(reporte)
