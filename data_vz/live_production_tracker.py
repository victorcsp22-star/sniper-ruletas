"""
========================================================================================
 MOTOR DE PRODUCCIÓN DIARIA Y LEDGER EN VIVO (LIVE FORWARD-TESTING TRACKER)
========================================================================================
Lleva el registro contable y operativo diario para los dos portafolios:
 1. Portafolio Venezuela (5 Ruletas: Lotto Activo, Granjita, Royal, Guacharo, Selva)
 2. Portafolio Brasil (2 Ruletas: Lotto Brasil, Lotto Bicho)

Características:
 - Replay cronológico estricto de sorteos para registrar cada señal de apuesta real.
 - Registro granular de cada disparo en ledger CSV (hora, ruleta, candidatos, apuesta, resultado, PnL).
 - Balance diario consolidado (Starting Bankroll, Ending Bankroll, Win Rate, ROI, MDD).
 - Monitoreo diario del Agente de Salud y estado de degradación de cada ruleta.
 - Persistencia segura en JSON y CSV independientes.
========================================================================================
"""

import datetime
import json
import os
import sys
from typing import Dict, List, Optional, Tuple
import pandas as pd

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Configuración de los 2 portafolios
PORTFOLIOS_CONFIG = {
    "venezuela": {
        "name": "Portafolio Venezuela (5 Ruletas)",
        "emoji": "🇻🇪",
        "state_file": os.path.join(BASE_DIR, "state_production_venezuela.json"),
        "ledger_file": os.path.join(BASE_DIR, "production_ledger_venezuela.csv"),
        "daily_file": os.path.join(BASE_DIR, "production_daily_venezuela.csv"),
        "default_bankroll": 1000.0,
        "mdd_floor": 0.40,
        "ruletas": {
            "Lotto Activo": {
                "file": os.path.join(BASE_DIR, "lotto_activo_2anios.csv"),
                "lags": [20, 18, 14],
                "payout": 30.0,
                "f_unit": 0.00900,
                "be_rate": 3.33,
                "emoji": "🦁"
            },
            "La Granjita": {
                "file": os.path.join(BASE_DIR, "la_granjita_2anios.csv"),
                "lags": [15, 17],
                "payout": 30.0,
                "f_unit": 0.00484,
                "be_rate": 3.33,
                "emoji": "🐸"
            },
            "Ruleta Royal": {
                "file": os.path.join(BASE_DIR, "ruleta_royal_2anios.csv"),
                "lags": [16, 19, 31],
                "payout": 30.0,
                "f_unit": 0.00826,
                "be_rate": 3.33,
                "emoji": "👑"
            },
            "Guacharo Activo": {
                "file": os.path.join(BASE_DIR, "guacharo_activo_2anios.csv"),
                "lags": [31, 41, 25, 42, 35],
                "payout": 60.0,
                "f_unit": 0.00680,
                "be_rate": 1.67,
                "emoji": "🦇"
            }
        }
    },
    "brasil": {
        "name": "Portafolio Brasil (2 Ruletas)",
        "emoji": "🇧🇷",
        "state_file": os.path.join(BASE_DIR, "state_production_brasil.json"),
        "ledger_file": os.path.join(BASE_DIR, "production_ledger_brasil.csv"),
        "daily_file": os.path.join(BASE_DIR, "production_daily_brasil.csv"),
        "default_bankroll": 200.0,
        "mdd_floor": 0.40,
        "ruletas": {
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
    }
}


def load_portfolio_state(portfolio_key: str) -> Dict:
    cfg = PORTFOLIOS_CONFIG[portfolio_key]
    state_file = cfg["state_file"]
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "portfolio": portfolio_key,
        "bankroll": cfg["default_bankroll"],
        "peak_capital": cfg["default_bankroll"],
        "mdd_floor": cfg["mdd_floor"],
        "last_processed_date": None,
        "last_processed_index": {},
        "streaks": {r: 0 for r in cfg["ruletas"]},
        "signals_history": {r: [] for r in cfg["ruletas"]}
    }


def clean_animal_name(name: str) -> str:
    """Corrige anomalías de codificación y estandariza nombres de animales."""
    if not isinstance(name, str):
        return ""
    name = name.strip()
    exact_map = {
        "AGUILA": "ÁGUILA",
        "ALACRAN": "ALACRÁN",
        "CAIMAN": "CAIMÁN",
        "CIEMPIES": "CIEMPIÉS",
        "DELFIN": "DELFÍN",
        "LEON": "LEÓN",
        "RATON": "RATÓN",
        "TIBURON": "TIBURÓN",
        "TUCAN": "TUCÁN",
        "BUFALO": "BÚFALO",
        "CHUGUIRE": "CHIGÜIRE",
        "CHIGUIRE": "CHIGÜIRE",
        "PUERCOESPIN": "PUERCOESPÍN",
        "CAMALEON": "CAMALEÓN",
        "GAVILAN": "GAVILÁN",
        "HIPOPOTAMO": "HIPOPÓTAMO",
        "ARANA": "ARAÑA",
    }
    return exact_map.get(name, name)


def save_portfolio_state(portfolio_key: str, state: Dict):
    cfg = PORTFOLIOS_CONFIG[portfolio_key]
    state_file = cfg["state_file"]
    try:
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error guardando estado de {portfolio_key}: {e}")

    # Sincronizar de forma espejo con bot_state.json o bot_state_brasil.json
    try:
        bot_state_file = os.path.join(BASE_DIR, "bot_state.json" if portfolio_key == "venezuela" else "bot_state_brasil.json")
        hist = state.get("historial_jugadas", [])
        losses_streak = 0
        for play in reversed(hist):
            if play.get("acierto", 0) == 1:
                break
            losses_streak += 1

        bot_state_payload = {
            "portfolio": portfolio_key,
            "bankroll": state["bankroll"],
            "peak_capital": state["peak_capital"],
            "losses_streak": losses_streak,
            "last_processed_date": state.get("last_processed_date"),
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p"),
            "total_jugadas": len(hist),
            "total_aciertos": sum(1 for p in hist if p.get("acierto", 0) == 1),
            "historial_jugadas": hist
        }
        with open(bot_state_file, "w", encoding="utf-8") as f:
            json.dump(bot_state_payload, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error sincronizando bot_state para {portfolio_key}: {e}")


def get_health_multiplier(recent_signals: List[bool], base_wr: float, be_rate: float) -> Tuple[float, str, float]:
    """Calcula la salud móvil (últimas 50 señales) y el factor de ponderación."""
    if not recent_signals:
        return 1.0, "Estándar (x1.00)", 100.0
    window = recent_signals[-50:]
    rec_hits = sum(window)
    rec_wr = (rec_hits / len(window) * 100.0) if len(window) > 0 else 0.0
    health_score = (rec_wr / base_wr * 100.0) if base_wr > 0 else 100.0

    if rec_wr < be_rate:
        return 0.35, "Defensivo (x0.35) [Bajo BE]", health_score
    elif health_score >= 100.0:
        return 1.20, "Prioritario (x1.20) [Óptimo]", health_score
    elif health_score >= 70.0:
        return 1.00, "Estándar (x1.00) [Normal]", health_score
    else:
        return 0.70, "Moderado (x0.70) [Fatiga]", health_score


def process_forward_production(portfolio_key: str, start_date: Optional[str] = "2026-10-01", up_to_date: Optional[str] = None):
    """
    Ejecuta el replay forward cronológico sorteo a sorteo desde start_date hasta up_to_date.
    Genera el ledger de apuestas y el resumen diario exacto.
    """
    cfg = PORTFOLIOS_CONFIG[portfolio_key]
    state = load_portfolio_state(portfolio_key)

    # 1. Cargar y ordenar todos los sorteos de las ruletas del portafolio
    all_draws = []
    ruletas_meta = cfg["ruletas"]

    for r_name, r_cfg in ruletas_meta.items():
        if not os.path.exists(r_cfg["file"]):
            continue
        df = pd.read_csv(r_cfg["file"], encoding="utf-8", dtype={"numero": str})
        df["numero"] = df["numero"].astype(str).str.strip()
        df["animal"] = df["animal"].astype(str).apply(clean_animal_name)
        df["_h"] = pd.to_datetime(df["hora"], format="%I:%M %p", errors="coerce").dt.time
        df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        df = df.sort_values(by="sort_dt").reset_index(drop=True)
        
        # Guardar en metadata el dataset completo y mapa de animales
        r_cfg["animals_map"] = dict(zip(df["numero"].astype(str).str.strip(), df["animal"].astype(str).str.strip()))
        r_cfg["df"] = df

    # Identificar fechas a procesar
    # Unir todas las fechas disponibles
    all_dates = set()
    for r_name, r_cfg in ruletas_meta.items():
        if "df" in r_cfg:
            all_dates.update(r_cfg["df"]["fecha"].unique().tolist())
    all_dates = sorted(list(all_dates))

    if start_date:
        all_dates = [d for d in all_dates if d >= start_date]
    if up_to_date:
        all_dates = [d for d in all_dates if d <= up_to_date]

    if not all_dates:
        print(f"[{portfolio_key}] No hay fechas para procesar en el rango solicitado.")
        return

    # Preparar estructuras de memoria
    if start_date and start_date <= "2026-09-14":
        bankroll = float(cfg["default_bankroll"])
        peak_capital = float(cfg["default_bankroll"])
    else:
        bankroll = float(state.get("bankroll", cfg["default_bankroll"]))
        peak_capital = float(state.get("peak_capital", cfg["default_bankroll"]))
    mdd_floor = state["mdd_floor"]

    ledger_rows = []
    historial_jugadas = []
    daily_summaries = []

    # Cargar ledger previo si existe
    if os.path.exists(cfg["ledger_file"]):
        try:
            df_old_ledger = pd.read_csv(cfg["ledger_file"])
            # Si reprocesamos desde start_date, descartar registros >= start_date para evitar duplicados
            if start_date:
                df_old_ledger = df_old_ledger[df_old_ledger["fecha"] < start_date]
                ledger_rows = df_old_ledger.to_dict("records")
        except Exception:
            pass

    # Inicializar rastreo de rachas y señales hasta justo antes de start_date
    streaks = {r: 0 for r in ruletas_meta}
    signals_hist = {r: [] for r in ruletas_meta}
    base_wrs = {}

    for r_name, r_cfg in ruletas_meta.items():
        df = r_cfg["df"]
        nums = df["numero"].tolist()
        lags = r_cfg["lags"]
        max_l = max(lags)
        
        # Calcular racha y señales antes de start_date
        prior_df = df[df["fecha"] < all_dates[0]]
        prior_nums = prior_df["numero"].tolist()
        
        cur_s = 0
        sig_list = []
        for i in range(max_l + 6, len(prior_nums)):
            act = prior_nums[i]
            rec6 = set(prior_nums[i-6:i])
            cands = list({prior_nums[i-l] for l in lags} - rec6)
            hit = (act in cands)
            if cands:
                if cur_s == 1:
                    sig_list.append(hit)
                if hit:
                    cur_s = 0
                else:
                    cur_s += 1
        
        streaks[r_name] = cur_s
        signals_hist[r_name] = sig_list
        base_wrs[r_name] = (sum(sig_list) / len(sig_list) * 100.0) if sig_list else 10.0

    # Procesar día a día
    for date_str in all_dates:
        day_bets_count = 0
        day_hits_count = 0
        day_invested = 0.0
        day_returned = 0.0
        day_start_bankroll = bankroll

        # Obtener todos los sorteos del día ordenados por hora
        day_draws = []
        for r_name, r_cfg in ruletas_meta.items():
            df_day = r_cfg["df"][r_cfg["df"]["fecha"] == date_str]
            for _, row in df_day.iterrows():
                day_draws.append({
                    "ruleta": r_name,
                    "fecha": row["fecha"],
                    "dia": row["dia"],
                    "hora": row["hora"],
                    "numero": str(row["numero"]),
                    "animal": str(row["animal"]),
                    "sort_dt": row["sort_dt"]
                })

        day_draws = sorted(day_draws, key=lambda x: x["sort_dt"])

        for draw in day_draws:
            r_name = draw["ruleta"]
            r_cfg = ruletas_meta[r_name]
            df_full = r_cfg["df"]
            
            # Encontrar índice de este sorteo en el historial completo de la ruleta
            match_idx = df_full[(df_full["fecha"] == draw["fecha"]) & (df_full["hora"] == draw["hora"])].index
            if len(match_idx) == 0:
                continue
            idx = match_idx[0]
            
            lags = r_cfg["lags"]
            if idx < max(lags) + 7:
                continue

            nums_up_to = df_full["numero"].iloc[:idx].tolist()
            actual_num = draw["numero"]
            actual_animal = draw["animal"]

            # Candidatos para este sorteo
            rec6 = set(nums_up_to[-6:])
            cands = list({nums_up_to[-l] for l in lags} - rec6)
            cost = len(cands)
            hit = (actual_num in cands)

            cur_streak = streaks[r_name]

            # ¿Dispara el Gatillo Post-Fallo 1?
            if cur_streak == 1 and cost > 0:
                # Calcular dimensión de apuesta
                peak = max(peak_capital, bankroll)
                floor = (1.0 - mdd_floor) * peak
                cushion = max(0.0, bankroll - floor)
                gz_mult = min(1.0, max(0.0, cushion / (mdd_floor * peak))) if (mdd_floor * peak) > 0 else 1.0

                hw, hw_label, _ = get_health_multiplier(signals_hist[r_name], base_wrs[r_name], r_cfg["be_rate"])
                
                # Apuesta unitaria
                base_stake = bankroll * r_cfg["f_unit"]
                bet_per_cand = round(max(0.10, base_stake * gz_mult * hw), 2)
                total_bet_cost = round(bet_per_cand * cost, 2)

                # Resultado
                if hit:
                    payout_amt = round(bet_per_cand * r_cfg["payout"], 2)
                    pnl = round(payout_amt - total_bet_cost, 2)
                    day_hits_count += 1
                else:
                    payout_amt = 0.0
                    pnl = -total_bet_cost

                bankroll = round(bankroll + pnl, 2)
                if bankroll > peak_capital:
                    peak_capital = bankroll

                day_bets_count += 1
                day_invested += total_bet_cost
                day_returned += payout_amt

                # Registrar en el historial de señales de salud
                signals_hist[r_name].append(hit)

                cur_dd = round(((peak_capital - bankroll) / peak_capital * 100.0), 2) if peak_capital > 0 else 0.0

                # Formatear candidatos con números y nombres de animales
                cands_formatted = [f"[{c:>2}] {r_cfg['animals_map'].get(str(c).strip(), 'ANIMAL')}" for c in cands]
                cands_names_str = ", ".join(cands_formatted)
                cands_str = "/".join(cands)
                actual_animal_clean = clean_animal_name(str(actual_animal))
                resultado_str = f"[{actual_num:>2}] {actual_animal_clean}"
                condicion_str = "🟢 GANADA" if hit else "🔴 PERDIDA"

                ledger_rows.append({
                    "fecha": draw["fecha"],
                    "hora": draw["hora"],
                    "ruleta": f"{r_cfg['emoji']} {r_name}",
                    "animales_seleccionados": cands_names_str,
                    "candidatos_codigos": cands_str,
                    "cant_cands": cost,
                    "apuesta_unitaria": bet_per_cand,
                    "costo_total": total_bet_cost,
                    "resultado_sorteo": resultado_str,
                    "resultado_num": actual_num,
                    "resultado_animal": actual_animal_clean,
                    "acierto": 1 if hit else 0,
                    "condicion": condicion_str,
                    "payout_cobrado": payout_amt,
                    "pnl": pnl,
                    "balance_cierre": bankroll,
                    "drawdown_pct": cur_dd
                })

                historial_jugadas.append({
                    "fecha": draw["fecha"],
                    "hora": draw["hora"],
                    "ruleta": f"{r_cfg['emoji']} {r_name}",
                    "animales_seleccionados": cands_formatted,
                    "animales_seleccionados_str": cands_names_str,
                    "candidatos_codigos": cands,
                    "resultado_sorteo": resultado_str,
                    "resultado_num": actual_num,
                    "resultado_animal": actual_animal_clean,
                    "acierto": 1 if hit else 0,
                    "condicion": condicion_str,
                    "apuesta_unitaria": bet_per_cand,
                    "costo_total": total_bet_cost,
                    "cobrado": payout_amt,
                    "pnl": pnl,
                    "balance_cierre": bankroll,
                    "drawdown_pct": cur_dd
                })

            # Actualizar racha virtual de la ruleta
            if hit:
                streaks[r_name] = 0
            else:
                streaks[r_name] = cur_streak + 1

        day_pnl = round(bankroll - day_start_bankroll, 2)
        day_pnl_pct = round((day_pnl / day_start_bankroll * 100.0), 2) if day_start_bankroll > 0 else 0.0
        day_wr = round((day_hits_count / day_bets_count * 100.0), 2) if day_bets_count > 0 else 0.0
        cur_dd = round(((peak_capital - bankroll) / peak_capital * 100.0), 2) if peak_capital > 0 else 0.0

        daily_summaries.append({
            "fecha": date_str,
            "balance_inicial": day_start_bankroll,
            "balance_final": bankroll,
            "pnl_neto": day_pnl,
            "pnl_pct": day_pnl_pct,
            "total_disparos": day_bets_count,
            "aciertos": day_hits_count,
            "win_rate": day_wr,
            "total_invertido": round(day_invested, 2),
            "total_retornado": round(day_returned, 2),
            "peak_historico": peak_capital,
            "drawdown_actual": cur_dd
        })

    # Guardar ledger completo en CSV
    df_ledger = pd.DataFrame(ledger_rows)
    df_ledger.to_csv(cfg["ledger_file"], index=False, encoding="utf-8")

    # Guardar resumen diario en CSV
    df_daily = pd.DataFrame(daily_summaries)
    df_daily.to_csv(cfg["daily_file"], index=False, encoding="utf-8")

    # Actualizar estado del portafolio
    state["bankroll"] = bankroll
    state["peak_capital"] = peak_capital
    state["last_processed_date"] = all_dates[-1]
    state["streaks"] = streaks
    state["signals_history"] = {r: signals_hist[r][-100:] for r in ruletas_meta}
    state["historial_jugadas"] = historial_jugadas
    save_portfolio_state(portfolio_key, state)

    return {
        "portfolio": portfolio_key,
        "name": cfg["name"],
        "emoji": cfg["emoji"],
        "df_daily": df_daily,
        "df_ledger": df_ledger,
        "historial_jugadas": historial_jugadas,
        "final_bankroll": bankroll,
        "peak_capital": peak_capital,
        "streaks": streaks,
        "base_wrs": base_wrs,
        "signals_hist": signals_hist
    }


def generate_production_report(vzla_res: Dict, br_res: Dict, output_md: str):
    """Genera el reporte consolidado diario en formato Markdown para el usuario."""
    df_d_vz = vzla_res["df_daily"]
    df_d_br = br_res["df_daily"]

    total_initial = 2000.0
    total_current = vzla_res["final_bankroll"] + br_res["final_bankroll"]
    total_net = total_current - total_initial
    total_roi = (total_net / total_initial * 100.0)

    last_date = df_d_vz["fecha"].iloc[-1] if not df_d_vz.empty else datetime.date.today().strftime("%Y-%m-%d")

    md = []
    md.append(f"# 📊 Auditoría de Producción Diaria (Live Forward-Testing)")
    md.append(f"> **Fecha de Inspección:** {last_date} | **Hora de Corte:** Sorteos Nocturnos Finalizados")
    md.append(f"> **Objetivo:** Seguimiento riguroso sorteo a sorteo en tiempo real de ambos bots en paralelo.")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 1. Resumen Ejecutivo Consolidado (Ambos Bots)")
    md.append("")
    md.append("| Métrica Global | 🇻🇪 Portafolio Venezuela (5 Ruletas) | 🇧🇷 Portafolio Brasil (2 Ruletas) | 🌐 Total Consolidado |")
    md.append("| :--- | :---: | :---: | :---: |")
    md.append(f"| **Capital Inicial** | $1,000.00 USD | $1,000.00 USD | $2,000.00 USD |")
    md.append(f"| **Capital Actual** | **${vzla_res['final_bankroll']:,.2f} USD** | **${br_res['final_bankroll']:,.2f} USD** | **${total_current:,.2f} USD** |")
    md.append(f"| **Beneficio Neto (PnL)** | **{'+' if vzla_res['final_bankroll']>=1000 else ''}{vzla_res['final_bankroll']-1000:,.2f} USD** | **{'+' if br_res['final_bankroll']>=1000 else ''}{br_res['final_bankroll']-1000:,.2f} USD** | **{'+' if total_net>=0 else ''}{total_net:,.2f} USD** ({total_roi:+.2f}%) |")
    md.append(f"| **Pico Histórico (ATH)** | ${vzla_res['peak_capital']:,.2f} USD | ${br_res['peak_capital']:,.2f} USD | ${vzla_res['peak_capital']+br_res['peak_capital']:,.2f} USD |")
    
    # Drawdowns
    dd_vz = ((vzla_res['peak_capital'] - vzla_res['final_bankroll']) / vzla_res['peak_capital'] * 100.0) if vzla_res['peak_capital'] > 0 else 0.0
    dd_br = ((br_res['peak_capital'] - br_res['final_bankroll']) / br_res['peak_capital'] * 100.0) if br_res['peak_capital'] > 0 else 0.0
    md.append(f"| **Drawdown Actual** | {dd_vz:.2f}% | {dd_br:.2f}% | {max(dd_vz, dd_br):.2f}% (Máx) |")
    
    # Totales disparos
    tot_bets_vz = df_d_vz["total_disparos"].sum() if not df_d_vz.empty else 0
    tot_hits_vz = df_d_vz["aciertos"].sum() if not df_d_vz.empty else 0
    wr_vz = (tot_hits_vz / tot_bets_vz * 100.0) if tot_bets_vz > 0 else 0.0

    tot_bets_br = df_d_br["total_disparos"].sum() if not df_d_br.empty else 0
    tot_hits_br = df_d_br["aciertos"].sum() if not df_d_br.empty else 0
    wr_br = (tot_hits_br / tot_bets_br * 100.0) if tot_bets_br > 0 else 0.0

    md.append(f"| **Total Disparos Sniper** | {tot_bets_vz:,} | {tot_bets_br:,} | {tot_bets_vz + tot_bets_br:,} |")
    md.append(f"| **Aciertos Globales** | {tot_hits_vz:,} ({wr_vz:.2f}%) | {tot_hits_br:,} ({wr_br:.2f}%) | {tot_hits_vz + tot_hits_br:,} ({(tot_hits_vz+tot_hits_br)/(tot_bets_vz+tot_bets_br)*100:.2f}%) |")
    md.append("")
    md.append("---")
    md.append("")

    # Tabla de producción diaria de los últimos 7 días
    md.append("## 2. Producción Diaria Detallada (Últimos Días)")
    md.append("")
    md.append("### 🇻🇪 Portafolio Venezuela (5 Ruletas en Paralelo)")
    md.append("")
    md.append("| Fecha | Balance Inicial | Balance Cierre | PnL Diario ($) | PnL Diario (%) | Disparos | Aciertos (WR%) | Drawdown |")
    md.append("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    for _, row in df_d_vz.tail(7).iterrows():
        sign = "+" if row["pnl_neto"] >= 0 else ""
        md.append(f"| {row['fecha']} | ${row['balance_inicial']:,.2f} | ${row['balance_final']:,.2f} | **{sign}${row['pnl_neto']:,.2f}** | {sign}{row['pnl_pct']:.2f}% | {int(row['total_disparos'])} | {int(row['aciertos'])} ({row['win_rate']:.1f}%) | {row['drawdown_actual']:.2f}% |")
    md.append("")

    md.append("### 🇧🇷 Portafolio Brasil (Lotto Brasil & Lotto Bicho)")
    md.append("")
    md.append("| Fecha | Balance Inicial | Balance Cierre | PnL Diario ($) | PnL Diario (%) | Disparos | Aciertos (WR%) | Drawdown |")
    md.append("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    for _, row in df_d_br.tail(7).iterrows():
        sign = "+" if row["pnl_neto"] >= 0 else ""
        md.append(f"| {row['fecha']} | ${row['balance_inicial']:,.2f} | ${row['balance_final']:,.2f} | **{sign}${row['pnl_neto']:,.2f}** | {sign}{row['pnl_pct']:.2f}% | {int(row['total_disparos'])} | {int(row['aciertos'])} ({row['win_rate']:.1f}%) | {row['drawdown_actual']:.2f}% |")
    md.append("")
    md.append("---")
    md.append("")

    # Estado de Salud y Rachas Actuales
    md.append("## 3. Estado Táctico y Agente de Salud por Ruleta al Cierre")
    md.append("")
    md.append("| Portafolio | Ruleta | Racha Fallos Actual | WR Reciente (50s) | Break-Even | Salud Edge | Estado Salud | Ponderación |")
    md.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
    
    for r_name, r_cfg in PORTFOLIOS_CONFIG["venezuela"]["ruletas"].items():
        s = vzla_res["streaks"].get(r_name, 0)
        hist = vzla_res["signals_hist"].get(r_name, [])
        bw = vzla_res["base_wrs"].get(r_name, 10.0)
        hw, hw_label, hscore = get_health_multiplier(hist, bw, r_cfg["be_rate"])
        rec_hits = sum(hist[-50:]) if hist else 0
        rec_len = len(hist[-50:]) if hist else 0
        rec_wr = (rec_hits / rec_len * 100.0) if rec_len > 0 else 0.0
        status = "🟢 Óptima" if hscore >= 100 else ("🟡 Normal" if rec_wr >= r_cfg["be_rate"] else "🔴 Degradada")
        md.append(f"| 🇻🇪 Venezuela | {r_cfg['emoji']} {r_name} | **{s}** | {rec_wr:.1f}% ({rec_hits}/{rec_len}) | {r_cfg['be_rate']:.2f}% | {hscore:.1f}% | {status} | {hw:.2f}x |")

    for r_name, r_cfg in PORTFOLIOS_CONFIG["brasil"]["ruletas"].items():
        s = br_res["streaks"].get(r_name, 0)
        hist = br_res["signals_hist"].get(r_name, [])
        bw = br_res["base_wrs"].get(r_name, 10.0)
        hw, hw_label, hscore = get_health_multiplier(hist, bw, r_cfg["be_rate"])
        rec_hits = sum(hist[-50:]) if hist else 0
        rec_len = len(hist[-50:]) if hist else 0
        rec_wr = (rec_hits / rec_len * 100.0) if rec_len > 0 else 0.0
        status = "🟢 Óptima" if hscore >= 100 else ("🟡 Normal" if rec_wr >= r_cfg["be_rate"] else "🔴 Degradada")
        md.append(f"| 🇧🇷 Brasil | {r_cfg['emoji']} {r_name} | **{s}** | {rec_wr:.1f}% ({rec_hits}/{rec_len}) | {r_cfg['be_rate']:.2f}% | {hscore:.1f}% | {status} | {hw:.2f}x |")

    md.append("")
    md.append("---")
    md.append("")
    md.append("## 4. Archivos de Auditoría Generados")
    md.append("- 📄 **Ledger Granular Venezuela:** `production_ledger_venezuela.csv`")
    md.append("- 📄 **Ledger Granular Brasil:** `production_ledger_brasil.csv`")
    md.append("- 📈 **Resumen Diario Venezuela:** `production_daily_venezuela.csv`")
    md.append("- 📈 **Resumen Diario Brasil:** `production_daily_brasil.csv`")

    content = "\n".join(md)
    with open(output_md, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"\n[✓] Reporte de producción guardado en: {output_md}")
    return content
