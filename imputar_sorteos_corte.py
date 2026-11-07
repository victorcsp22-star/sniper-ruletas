"""
========================================================================================
 MOTOR DE IMPUTACIÓN Y AUDITORÍA DE TRADING CONTINUO 24/7 (SIMULACIÓN REAL SIN CORTES)
========================================================================================
Reconstruye e imputa en el ledger oficial y diario de operaciones todos los disparos
válidos ocurridos durante cortes de luz o desconexiones, garantizando que el demo
opere exactamente como lo haría en un servidor VPS 24/7.
========================================================================================
"""

import os
import sys
import datetime
import pandas as pd
from typing import Dict, List, Tuple

from config import (
    BASE_DIR,
    RULETAS_CONFIG,
    LEDGER_FILE,
    DIARIO_FILE,
    STATE_FILE,
    MIN_BET,
    QUARANTINE_MISSES,
    TARGET_MDD,
    WEEKLY_CIRCUIT_BREAKER_PCT,
    WEEKLY_KELLY_MULTIPLIER,
    SMART_INVESTMENT_ENABLED,
    REBOUND_BOOST_MULTIPLIER,
    FATIGUE_DISCOUNT_MULTIPLIER,
    NEUTRAL_MULTIPLIER,
)
from bot_nuevas_ruletas import (
    load_state,
    save_state,
    get_history_series,
    record_to_ledger,
    append_to_markdown_journal,
    manage_weekly_cycle,
    get_rebound_momentum_multiplier,
)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
    except Exception:
        pass


def run_continuous_simulation():
    state = load_state()
    state = manage_weekly_cycle(state)
    bankroll = state.get("bankroll", 265.11)
    peak = state.get("peak_bankroll", bankroll)
    cycle_base = state.get("cycle_start_bankroll", 200.0)

    # Cargar ledger existente para verificar duplicados
    existing_keys = set()
    if os.path.exists(LEDGER_FILE):
        ldf = pd.read_csv(LEDGER_FILE)
        for _, r in ldf.iterrows():
            key = (str(r["fecha"]).strip(), str(r["hora"]).strip(), str(r["ruleta"]).strip())
            existing_keys.add(key)

    # Identificar todas las señales históricas válidas
    all_signals = []

    for r_name, cfg in RULETAS_CONFIG.items():
        if not cfg.get("active", False):
            continue

        nums, df = get_history_series(r_name)
        lags = cfg["lags"]
        rec_w = cfg.get("rec_w", 6)
        target_streaks = cfg.get("target_streaks", [1])
        use_anti_cluster = cfg.get("anti_clustering", False)
        min_idx = max(lags) + max(rec_w, 8)

        # Mapeo a nombre de animalito
        num_to_animal = {str(row["numero"]): str(row["animal"]) for _, row in df.iterrows()}

        streak = 0
        trigger_misses = 0
        seen_today = set()
        prev_date = None
        prev_was_repeat = False
        dates = df["fecha"].tolist()

        for i in range(min_idx, len(nums)):
            actual = nums[i]
            d = dates[i]
            hora = df.iloc[i]["hora"]
            sort_dt = df.iloc[i]["sort_dt"]

            if d != prev_date:
                prev_date = d
                seen_today = set()
                prev_was_repeat = False

            rec_set = set(nums[i-rec_w:i])
            cands = sorted(list({nums[i-l] for l in lags if i >= l} - rec_set))
            is_repeat_now = (actual in seen_today)
            skip_shot = bool(use_anti_cluster and prev_was_repeat)

            # Evaluar si ocurrió a partir del lunes 19 a las 12:00 PM
            if d in ["2026-10-19", "2026-10-20"]:
                is_quarantined = bool(QUARANTINE_MISSES > 0 and trigger_misses >= QUARANTINE_MISSES)
                if streak in target_streaks and cands and not skip_shot and not is_quarantined:
                    hit = (actual in cands)
                    anim_salido = num_to_animal.get(actual, df.iloc[i]["animal"])
                    all_signals.append({
                        "sort_dt": sort_dt,
                        "fecha": d,
                        "hora": hora,
                        "ruleta": r_name,
                        "cands": cands,
                        "cands_str": ", ".join([f"#{c} {num_to_animal.get(c, '')}" for c in cands]),
                        "cands_count": len(cands),
                        "salido_num": actual,
                        "salido_anim": anim_salido,
                        "hit": hit,
                        "cfg": cfg,
                        "trigger_misses": trigger_misses,
                    })

            # Actualizar racha y misses
            if cands and not skip_shot:
                hit = (actual in cands)
                if streak in target_streaks:
                    if hit:
                        trigger_misses = 0
                    else:
                        trigger_misses += 1
                streak = 0 if hit else streak + 1
            elif cands and skip_shot:
                hit = (actual in cands)
                streak = 0 if hit else streak + 1

            seen_today.add(actual)
            prev_was_repeat = is_repeat_now

    # Ordenar cronológicamente todas las señales detectadas
    all_signals = sorted(all_signals, key=lambda x: x["sort_dt"])

    print(f"Total señales históricas encontradas en rango: {len(all_signals)}")

    imputed_count = 0

    for sig in all_signals:
        key = (sig["fecha"], sig["hora"], sig["ruleta"])
        if key in existing_keys:
            # Ya fue procesado en el ledger
            continue

        r_name = sig["ruleta"]
        cfg = sig["cfg"]
        cands_count = sig["cands_count"]
        hit = sig["hit"]
        salido_num = sig["salido_num"]
        salido_anim = sig["salido_anim"]
        fecha_res = sig["fecha"]
        hora_res = sig["hora"]

        # Calcular stake exacto
        smart_mult, smart_label = get_rebound_momentum_multiplier(sig["trigger_misses"])
        f_u = cfg.get("f_unit", 0.008)
        eff_kelly = state.get("effective_kelly", 0.1744)
        base_stake = state.get("weekly_fixed_stakes", {}).get(
            r_name,
            round(max(MIN_BET, cycle_base * f_u * eff_kelly), 2)
        )
        stake_unit = base_stake
        cost = round(cands_count * stake_unit, 2)
        payout = cfg["payout"]
        cobrado = round(stake_unit * payout, 2) if hit else 0.0
        pnl = round(cobrado - cost, 2)

        bankroll = round(bankroll + pnl, 2)
        peak = max(peak, bankroll)
        dd_pct = ((peak - bankroll) / peak * 100.0) if peak > 0 else 0.0

        state["bankroll"] = bankroll
        state["peak_bankroll"] = peak
        state["total_invested"] = round(state.get("total_invested", 0.0) + cost, 2)
        state["total_collected"] = round(state.get("total_collected", 0.0) + cobrado, 2)
        state["total_pnl"] = round(state.get("total_pnl", 0.0) + pnl, 2)

        if hit:
            state["wins"] = state.get("wins", 0) + 1
        else:
            state["losses"] = state.get("losses", 0) + 1

        event = {
            "timestamp": f"{fecha_res} {hora_res}",
            "fecha": fecha_res,
            "hora": hora_res,
            "ruleta": r_name,
            "candidatos": sig["cands_str"],
            "cands_count": cands_count,
            "zona_patron": smart_label,
            "smart_mult": smart_mult,
            "stake_unit": stake_unit,
            "total_bet": cost,
            "resultado": f"[{salido_num}] {salido_anim}",
            "condicion": "🟢 GANADA" if hit else "🔴 PERDIDA",
            "cobrado": cobrado,
            "pnl": pnl,
            "saldo": bankroll,
            "peak": peak,
            "drawdown_pct": round(dd_pct, 2),
            "salido_num": salido_num,
            "salido_anim": salido_anim,
            "hit": hit,
            "inv": cost,
            "cob": cobrado,
            "bankroll": bankroll
        }

        record_to_ledger(event)
        append_to_markdown_journal(event, state)
        existing_keys.add(key)
        imputed_count += 1

        print(f"  ⚡ IMPUTADO: {fecha_res} {hora_res} | {r_name} | Jugados: {sig['cands_str']} | Salido: #{salido_num} {salido_anim} | PnL: {pnl:+.2f} USD | Nuevo Saldo: ${bankroll:,.2f} USD")

    save_state(state)
    print(f"\n✅ Proceso completado. {imputed_count} disparos imputados exitosamente.")
    print(f"   Saldo Final Consolidado: ${bankroll:,.2f} USD | Peak: ${peak:,.2f} USD | Drawdown: {((peak-bankroll)/peak*100.0):.2f}%")


if __name__ == "__main__":
    run_continuous_simulation()
