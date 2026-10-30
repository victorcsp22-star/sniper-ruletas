"""
========================================================================================
 SERVIDOR BACKEND MÓVIL (API REST + PWA NATIVA ANDROID)
========================================================================================
Expone la lógica cuántica en tiempo real para la App Móvil:
 - Sincronización en vivo con TuAzar bajo demanda (en 1 segundo).
 - Cálculo de señales activas inmediatas ($1.00 USD fijo por animalito).
 - Radar táctico de las 7 ruletas y conteo de fallos.
 - Balance de billetera (Saldo en mesa, ganancias retiradas, patrimonio total).
========================================================================================
"""

import os
import sys
import json
import datetime
from typing import Dict, List
from flask import Flask, jsonify, request, send_from_directory

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from config import (
    RULETAS_CONFIG,
    STATE_FILE,
    LEDGER_FILE,
    FIXED_STAKE_UNIT,
)
from bot_nuevas_ruletas import (
    load_state,
    save_state,
    get_history_series,
    calculate_current_streak_and_misses,
    generate_upcoming_candidates,
    fetch_live_results,
    update_local_csvs,
)
from live_auditor_engine import LIVE_AUDITOR
from reporte_horario import generate_hourly_report

app = Flask(__name__, static_folder="static", static_url_path="")


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/status", methods=["GET"])
def get_status():
    """Retorna el estado táctico completo del sistema para la pantalla del celular."""
    try:
        state = load_state()
        bankroll = state.get("bankroll", 200.0)
        withdrawn = state.get("total_withdrawn", 0.0)
        patrimonio = round(bankroll + withdrawn, 2)
        cycle_num = state.get("cycle_number", 5)
        cycle_base = state.get("cycle_start_bankroll", 200.0)
        cycle_pnl = round(bankroll - cycle_base, 2)
        cycle_pct = round((cycle_pnl / cycle_base * 100.0) if cycle_base > 0 else 0.0, 1)

        today_str = datetime.date.today().strftime("%Y-%m-%d")

        # Cargar ledger de hoy
        ops_today = 0
        wins_today = 0
        inv_today = 0.0
        cob_today = 0.0
        recent_ledger = []
        if os.path.exists(LEDGER_FILE):
            import pandas as pd
            df_leg = pd.read_csv(LEDGER_FILE)
            df_today = df_leg[df_leg["fecha"].astype(str) == today_str]
            ops_today = len(df_today)
            wins_today = sum(1 for _, row in df_today.iterrows() if float(row.get("pnl", 0.0)) > 0)
            inv_today = sum(float(row.get("total_bet", 0.0)) for _, row in df_today.iterrows())
            cob_today = sum(float(row.get("cobrado", 0.0)) for _, row in df_today.iterrows())
            recent_ledger = df_today.tail(8).to_dict(orient="records")

        pnl_today = round(cob_today - inv_today, 2)

        # Generar radar y señales activas
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
            last_salido = cands_info.get("last_salido_str", "---")

            # Cálculo de urgencia y conteo
            target_streaks = cfg.get("target_streaks", [1])
            min_target = min(target_streaks)
            
            if is_markov:
                badge = "⚡ Markov Sniper"
                conteo_str = "🚨 ¡DISPARAR MARKOV! (1)"
                urgencia = 1
            elif stk in target_streaks and not is_anti_blocked:
                badge = f"🔥 Racha {stk} (Objetivo)"
                conteo_str = "🚨 ¡DISPARAR AHORA! (0)"
                urgencia = 1
            elif is_anti_blocked:
                badge = "🛡️ AntiCluster"
                conteo_str = "🛡️ Bloqueado por Repetición"
                urgencia = 3
            elif stk < min_target:
                f_falta = min_target - stk
                badge = "🟢 Racha 0" if stk == 0 else f"🟡 Racha {stk}"
                conteo_str = f"⚠️ Falta {f_falta} fallo"
                urgencia = 2
            else:
                badge = f"🟡 Racha {stk}"
                conteo_str = f"💤 Espera reinicio ({stk})"
                urgencia = 3

            # Si hay disparo activo
            if (stk in target_streaks and not is_anti_blocked) or is_markov:
                costo = round(len(cands) * FIXED_STAKE_UNIT, 2)
                premio = round(FIXED_STAKE_UNIT * cfg["payout"], 2)
                active_signals.append({
                    "ruleta": r_name,
                    "emoji": cfg["emoji"],
                    "tipo": "⚡ Markov Sniper" if is_markov else "🎯 Canasta Rezagados",
                    "candidatos": cands,
                    "candidatos_str": ", ".join([f"#{c['numero']} {c['animal']}" for c in cands]),
                    "total_fichas": len(cands),
                    "costo": costo,
                    "premio_potencial": premio,
                    "payout": cfg["payout"],
                    "ultimo_salido": last_salido
                })

            radar_items.append({
                "ruleta": r_name,
                "emoji": cfg["emoji"],
                "payout": cfg["payout"],
                "racha": stk,
                "misses": miss,
                "badge": badge,
                "conteo_str": conteo_str,
                "urgencia": urgencia,
                "ultimo_salido": last_salido,
                "is_markov": is_markov,
                "is_anti_blocked": is_anti_blocked
            })

        radar_items.sort(key=lambda x: (x["urgencia"], x["racha"]))

        return jsonify({
            "status": "ok",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
            "hora": datetime.datetime.now().strftime("%I:%M %p").lstrip("0"),
            "wallet": {
                "bankroll": bankroll,
                "withdrawn": withdrawn,
                "patrimonio": patrimonio,
                "cycle_num": cycle_num,
                "cycle_base": cycle_base,
                "cycle_pnl": cycle_pnl,
                "cycle_pct": cycle_pct,
                "pnl_today": pnl_today,
                "ops_today": ops_today,
                "wins_today": wins_today,
                "inv_today": inv_today,
                "cob_today": cob_today,
                "win_rate_today": round(wins_today / ops_today * 100.0, 1) if ops_today > 0 else 0.0
            },
            "active_signals": active_signals,
            "radar_items": radar_items,
            "recent_ledger": recent_ledger
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/sync", methods=["POST"])
def sync_tuazar():
    """Descarga los últimos resultados de TuAzar en tiempo real y actualiza los CSV locales."""
    try:
        live_data = fetch_live_results()
        new_counts = update_local_csvs(live_data)
        total_new = sum(new_counts.values())
        return jsonify({
            "status": "ok",
            "total_new_draws": total_new,
            "new_counts": new_counts,
            "synced_at": datetime.datetime.now().strftime("%I:%M:%S %p")
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/reporte", methods=["GET"])
def get_reporte():
    """Retorna el reporte táctico horario completo formateado."""
    try:
        txt = generate_hourly_report()
        return jsonify({"status": "ok", "reporte": txt})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=" * 80)
    print("🚀 SERVIDOR MÓVIL INICIADO — LISTO PARA CONECTARSE DESDE EL CELULAR")
    print(f"   • En esta PC:       http://localhost:{port}")
    print("=" * 80)
    app.run(host="0.0.0.0", port=port, debug=False)
