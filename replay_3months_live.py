"""
========================================================================================
 MOTOR DE REPLAY EN VIVO (3 MESES: 15-JUL-2026 AL 15-OCT-2026)
========================================================================================
Simula cronológicamente la ejecución en vivo del bot durante los últimos 3 meses:
 - Cartera Oficial: 7 Ruletas (Lotto Activo, Granjita, Royal, Guácharo, Gatazo, Mega Animal, Monje).
 - Capital Inicial: $200.00 USD (15 de Julio de 2026).
 - Gestión de Capital: Full Kelly con Colchón Grossman-Zhou (MDD Floor 40%, Min bet $0.10).
 - Genera:
    1. state_nuevas_ruletas.json (Estado actual del bot listo para continuar operando en vivo).
    2. ledger_nuevas_ruletas.csv (Historial granular de cada disparo).
    3. diario_nuevas_ruletas.md (Diario visual Markdown organizado por día con números jugados,
       costo de la jugada, resultado oficial, ganada/perdida y saldo progresivo).
========================================================================================
"""

import os
import sys
import datetime
import json
import pandas as pd
import numpy as np

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
        "card_title": "Lotto Activo",
        "lags": [20, 18, 14],
        "payout": 30.0,
        "f_unit": 0.00900,
        "be_rate": 3.33,
        "target_streaks": [1],
        "emoji": "🦁"
    },
    "La Granjita": {
        "file": os.path.join(VZ_DIR, "la_granjita_2anios.csv"),
        "card_title": "La Granjita",
        "lags": [15, 17],
        "payout": 30.0,
        "f_unit": 0.00484,
        "be_rate": 3.33,
        "target_streaks": [1],
        "emoji": "🐸"
    },
    "Ruleta Royal": {
        "file": os.path.join(VZ_DIR, "ruleta_royal_2anios.csv"),
        "card_title": "Ruleta Royal",
        "lags": [16, 19, 31],
        "payout": 30.0,
        "f_unit": 0.00826,
        "be_rate": 3.33,
        "target_streaks": [1],
        "emoji": "👑"
    },
    "Guacharo Activo": {
        "file": os.path.join(VZ_DIR, "guacharo_activo_2anios.csv"),
        "card_title": "Guácharo Activo",
        "lags": [31, 41, 25, 42, 35],
        "payout": 60.0,
        "f_unit": 0.00680,
        "be_rate": 1.67,
        "target_streaks": [1],
        "emoji": "🦇"
    },
    "Gatazo": {
        "file": os.path.join(NEW_DIR, "gatazo.csv"),
        "card_title": "Gatazo",
        "lags": [35, 22, 20],
        "payout": 60.0,
        "f_unit": 0.00900,
        "be_rate": 1.67,
        "target_streaks": [1, 2],
        "emoji": "🐯"
    },
    "Mega Animal 40": {
        "file": os.path.join(NEW_DIR, "mega_animal_40.csv"),
        "card_title": "Mega Animal 40",
        "lags": [18, 21, 37],
        "payout": 30.0,
        "f_unit": 0.00800,
        "be_rate": 3.33,
        "target_streaks": [1],
        "emoji": "🦏"
    },
    "Monje Millonario": {
        "file": os.path.join(NEW_DIR, "monje_millonario.csv"),
        "card_title": "Monje Millonario",
        "lags": [24, 35, 37],
        "payout": 60.0,
        "f_unit": 0.00700,
        "be_rate": 1.67,
        "target_streaks": [1],
        "emoji": "🧘‍♂️"
    }
}

START_DATE = "2026-07-15"
INITIAL_BANKROLL = 200.0
MDD_FLOOR = 0.40
MIN_BET = 0.10

def replay_live():
    # 1. Cargar datos y extraer eventos
    all_events = []
    animal_maps = {}

    for r_name, cfg in CONFIG_7.items():
        if not os.path.exists(cfg["file"]):
            print(f"⚠️ Archivo no encontrado: {cfg['file']}")
            continue

        df = pd.read_csv(cfg["file"], dtype={"numero": str})
        df["numero"] = df["numero"].astype(str).str.strip()
        df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        df = df.sort_values(by="sort_dt").reset_index(drop=True)

        a_map = {}
        for _, row in df.iterrows():
            a_map[str(row["numero"])] = row["animal"]
        animal_maps[r_name] = a_map

        lags = cfg["lags"]
        payout = cfg["payout"]
        f_unit = cfg["f_unit"]
        target_streaks = cfg["target_streaks"]
        nums = df["numero"].tolist()
        min_idx = max(lags) + 6

        streak = 0
        trigger_misses = 0
        for i in range(min_idx, len(nums)):
            fecha = df.iloc[i]["fecha"]
            hora = df.iloc[i]["hora"]
            actual = nums[i]
            actual_anim = a_map.get(actual, "DESCONOCIDO")
            rec6 = set(nums[i-6:i])
            cands = sorted(list({nums[i-l] for l in lags} - rec6))

            if cands:
                cost_units = len(cands)
                hit = (actual in cands)

                # Si es racha objetivo
                if streak in target_streaks:
                    cur_misses = trigger_misses
                    if fecha >= START_DATE:
                        cands_detail = [{"num": c, "anim": a_map.get(c, "DESCONOCIDO")} for c in cands]
                        all_events.append({
                            "dt": df.iloc[i]["sort_dt"],
                            "fecha": fecha,
                            "hora": hora,
                            "ruleta": r_name,
                            "emoji": cfg["emoji"],
                            "payout": payout,
                            "f_unit": f_unit,
                            "cands": cands_detail,
                            "cands_codes": cands,
                            "cands_count": cost_units,
                            "actual_num": actual,
                            "actual_anim": actual_anim,
                            "hit": hit,
                            "trigger_misses": cur_misses
                        })
                    if hit:
                        trigger_misses = 0
                    else:
                        trigger_misses += 1

                if hit:
                    streak = 0
                else:
                    streak += 1

    # Ordenar cronológicamente todos los disparos
    all_events.sort(key=lambda x: x["dt"])

    # 2. Ejecutar replay en vivo con Grossman-Zhou + Rebound Momentum
    bankroll = INITIAL_BANKROLL
    peak = INITIAL_BANKROLL
    total_inv = 0.0
    total_cob = 0.0
    wins = 0
    losses = 0

    ledger_rows = []
    daily_groups = {}

    for ev in all_events:
        # Grossman-Zhou sizing + Rebound Momentum
        peak = max(peak, bankroll)
        floor = (1.0 - MDD_FLOOR) * peak
        cushion = max(0.0, bankroll - floor)
        gz_mult = min(1.0, max(0.0, cushion / (MDD_FLOOR * peak))) if (MDD_FLOOR * peak) > 0 else 1.0

        misses = ev.get("trigger_misses", 0)
        if 1 <= misses <= 3:
            smart_mult = 1.25
            zona_label = "🔥 Rebote 1.25x"
        elif misses == 0:
            smart_mult = 0.85
            zona_label = "🛡️ Fatiga 0.85x"
        else:
            smart_mult = 1.00
            zona_label = "⚖️ Neutral 1.00x"

        base_stake = bankroll * ev["f_unit"]
        stake_unit = round(max(MIN_BET, base_stake * gz_mult * smart_mult), 2)
        total_bet = round(stake_unit * ev["cands_count"], 2)

        if ev["hit"]:
            cobrado = round(stake_unit * ev["payout"], 2)
            pnl = round(cobrado - total_bet, 2)
            wins += 1
            condicion = "🟢 GANADA"
        else:
            cobrado = 0.0
            pnl = -total_bet
            losses += 1
            condicion = "🔴 PERDIDA"

        bankroll = round(bankroll + pnl, 2)
        total_inv = round(total_inv + total_bet, 2)
        total_cob = round(total_cob + cobrado, 2)
        cur_dd = round(((peak - bankroll) / peak * 100.0) if peak > 0 else 0.0, 2)

        cands_str = ", ".join([f"[{c['num']}] {c['anim']}" for c in ev["cands"]])
        res_str = f"[{ev['actual_num']}] {ev['actual_anim']}"

        row_data = {
            "fecha": ev["fecha"],
            "hora": ev["hora"],
            "ruleta": f"{ev['emoji']} {ev['ruleta']}",
            "candidatos": cands_str,
            "cands_count": ev["cands_count"],
            "zona_patron": zona_label,
            "smart_mult": smart_mult,
            "stake_unit": stake_unit,
            "total_bet": total_bet,
            "resultado": res_str,
            "condicion": condicion,
            "cobrado": cobrado,
            "pnl": pnl,
            "saldo": bankroll,
            "peak": peak,
            "drawdown_pct": cur_dd
        }
        ledger_rows.append(row_data)

        f_key = ev["fecha"]
        if f_key not in daily_groups:
            daily_groups[f_key] = []
        daily_groups[f_key].append(row_data)

    # 3. Guardar ledger_nuevas_ruletas.csv
    df_ledger = pd.DataFrame(ledger_rows)
    ledger_path = os.path.join(NEW_DIR, "ledger_nuevas_ruletas.csv")
    df_ledger.to_csv(ledger_path, index=False, encoding="utf-8")
    print(f"✅ Ledger guardado: {ledger_path} ({len(df_ledger)} registros)")

    # 4. Calcular rachas finales actuales de cada ruleta para state_nuevas_ruletas.json
    final_streaks = {}
    final_misses = {}
    last_draws = {}
    for r_name, cfg in CONFIG_7.items():
        df_r = pd.read_csv(cfg["file"], dtype={"numero": str})
        df_r["numero"] = df_r["numero"].astype(str).str.strip()
        df_r["sort_dt"] = pd.to_datetime(df_r["fecha"] + " " + df_r["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        df_r = df_r.sort_values(by="sort_dt").reset_index(drop=True)
        nums_r = df_r["numero"].tolist()
        lags_r = cfg["lags"]
        target_streaks_r = cfg.get("target_streaks", [1])
        min_idx_r = max(lags_r) + 6

        s_cur = 0
        m_cur = 0
        for idx in range(min_idx_r, len(nums_r)):
            act_n = nums_r[idx]
            rec_6 = set(nums_r[idx-6:idx])
            c_lst = list({nums_r[idx-l] for l in lags_r} - rec_6)
            if c_lst:
                hit_n = (act_n in c_lst)
                if s_cur in target_streaks_r:
                    if hit_n:
                        m_cur = 0
                    else:
                        m_cur += 1
                s_cur = 0 if hit_n else (s_cur + 1)
        final_streaks[r_name] = s_cur
        final_misses[r_name] = m_cur
        last_row = df_r.iloc[-1]
        last_draws[r_name] = f"{last_row['fecha']} {last_row['hora']} -> #{last_row['numero']} {last_row['animal']}"

    # 5. Guardar state_nuevas_ruletas.json
    state_data = {
        "portfolio": "cartera_unificada_7ruletas",
        "bankroll": bankroll,
        "initial_bankroll": INITIAL_BANKROLL,
        "peak_bankroll": peak,
        "mdd_floor": MDD_FLOOR,
        "min_bet": MIN_BET,
        "sizing_model": "grossman_zhou_rebound_momentum",
        "simulation_start_date": START_DATE,
        "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p"),
        "total_jugadas": len(ledger_rows),
        "total_aciertos": wins,
        "total_fallos": losses,
        "win_rate": round(wins / len(ledger_rows) * 100.0, 2) if ledger_rows else 0.0,
        "total_invested": total_inv,
        "total_collected": total_cob,
        "total_pnl": round(total_cob - total_inv, 2),
        "roi_neto": round((total_cob - total_inv) / total_inv * 100.0, 2) if total_inv > 0 else 0.0,
        "streaks": final_streaks,
        "trigger_misses": final_misses,
        "last_seen_draw": last_draws
    }

    state_path = os.path.join(NEW_DIR, "state_nuevas_ruletas.json")
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Estado guardado: {state_path}")

    # 6. Generar diario_nuevas_ruletas.md (Registro visual día a día)
    diario_path = os.path.join(NEW_DIR, "diario_nuevas_ruletas.md")
    diario_art_path = os.path.join(ARTIFACT_DIR, "diario_nuevas_ruletas.md")

    with open(diario_path, "w", encoding="utf-8") as f:
        f.write("# 📓 Diario de Operaciones en Vivo: Cartera Oficial de 7 Ruletas\n\n")
        f.write("> **Ubicación:** `C:\\Users\\victo\\nuevas_ruletas\\`  \n")
        f.write(f"> **Período de Operación en Vivo:** 15 de Julio de 2026 al 15 de Octubre de 2026 (3 Meses)  \n")
        f.write(f"> **Capital Inicial:** ${INITIAL_BANKROLL:,.2f} USD  \n")
        f.write(f"> **Capital Actual al Cierre:** **${bankroll:,.2f} USD** (+${bankroll - INITIAL_BANKROLL:,.2f} USD netos)  \n")
        f.write(f"> **Modelo de Gestión:** Full Kelly + Colchón Grossman-Zhou + Inversión Inteligente Rebound Momentum.  \n")
        f.write(f"> **Estrategia:** Gatillo Sniper Post-Fallo con Filtro de Recencia Intra-Día 6h.  \n\n")

        f.write("## 🏆 Resumen General de los 3 Meses en Vivo\n\n")
        f.write(f"| Métrica Clave | Resultado de los 3 Meses |\n")
        f.write(f"| :--- | :---: |\n")
        f.write(f"| **Sorteos Jugados (Disparos Sniper)** | **{len(ledger_rows):,} jugadas** |\n")
        f.write(f"| **🟢 Sorteos Ganados (Aciertos)** | **{wins:,} aciertos** ({wins/len(ledger_rows)*100:.2f}% Win Rate) |\n")
        f.write(f"| **🔴 Sorteos Perdidos (Fallos)** | **{losses:,} fallos** |\n")
        f.write(f"| **Capital Total Invertido** | **${total_inv:,.2f} USD** |\n")
        f.write(f"| **Capital Total Cobrado / Premios** | **${total_cob:,.2f} USD** |\n")
        f.write(f"| **💰 Beneficio Neto (PnL)** | **+${total_cob - total_inv:,.2f} USD** |\n")
        f.write(f"| **📈 Rentabilidad Neta (ROI)** | **+{(total_cob - total_inv)/total_inv*100:.2f}%** |\n")
        f.write(f"| **🚀 Multiplicador de Capital** | **{bankroll/INITIAL_BANKROLL:.2f}x** (de $200 a ${bankroll:,.2f}) |\n")
        f.write(f"| **Pico Máximo de Capital (ATH)** | **${peak:,.2f} USD** |\n")
        f.write(f"| **Máximo Drawdown Registrado** | **{df_ledger['drawdown_pct'].max():.2f}%** |\n\n")

        f.write("---\n\n")
        f.write("## 📜 Registro Granular de Cada Jugada (Día por Día)\n\n")

        running_day_cum = INITIAL_BANKROLL
        for f_date, day_events in sorted(daily_groups.items()):
            day_inv = sum(e["total_bet"] for e in day_events)
            day_cob = sum(e["cobrado"] for e in day_events)
            day_pnl = day_cob - day_inv
            day_hits = sum(1 for e in day_events if e["condicion"] == "🟢 GANADA")
            close_saldo = day_events[-1]["saldo"]

            pnl_badge = "+" if day_pnl >= 0 else ""
            f.write(f"### 📅 {f_date} (Disparos: {len(day_events)} | Aciertos: {day_hits} | PnL Día: {pnl_badge}${day_pnl:,.2f} | Saldo: ${close_saldo:,.2f})\n\n")
            f.write("| Hora | Ruleta | Condición Patrón | Animales Seleccionados | Total Jugada ($) | Salido Oficial | Resultado | Cobrado ($) | PnL Jugada | Saldo Cierre |\n")
            f.write("| :---: | :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")

            for e in day_events:
                pnl_j = f"{'+' if e['pnl']>=0 else ''}${e['pnl']:.2f}"
                f.write(f"| {e['hora']} | {e['ruleta']} | {e['zona_patron']} | `{e['candidatos']}` | ${e['total_bet']:.2f} | **{e['resultado']}** | {e['condicion']} | ${e['cobrado']:.2f} | **{pnl_j}** | **${e['saldo']:,.2f}** |\n")
            f.write("\n")

    # Copiar a artefactos
    try:
        os.makedirs(ARTIFACT_DIR, exist_ok=True)
        with open(diario_path, "r", encoding="utf-8") as src, open(diario_art_path, "w", encoding="utf-8") as dst:
            dst.write(src.read())
        print(f"✅ Diario visual copiado a artefactos: {diario_art_path}")
    except Exception as e:
        print(f"⚠️ Error copiando diario a artefactos: {e}")

    # Retornar resumen
    return state_data

if __name__ == "__main__":
    st = replay_live()
    print("=" * 115)
    print(" 🌟 RESUMEN DE LOS 3 MESES OPERANDO EN VIVO (15-JUL AL 15-OCT-2026)")
    print("=" * 115)
    print(f"  • Capital Inicial (15-Jul-2026):               ${st['initial_bankroll']:,.2f} USD")
    print(f"  • Capital Final Actual (15-Oct-2026 6:00 PM):   ${st['bankroll']:,.2f} USD")
    print(f"  • 💰 GANANCIA NETA LIMPIA (PnL):                +${st['total_pnl']:,.2f} USD")
    print(f"  • 📈 RENTABILIDAD NETA (ROI):                   +{st['roi_neto']:.2f}%")
    print(f"  • 🚀 Multiplicador de Capital:                  {st['bankroll']/st['initial_bankroll']:.2f}x")
    print(f"  • Total Disparos Operados:                      {st['total_jugadas']:,} jugadas")
    print(f"  • 🟢 Aciertos / Ganadas:                         {st['total_aciertos']:,} ({st['win_rate']:.2f}% WR)")
    print(f"  • 🔴 Fallos / Perdidas:                          {st['total_fallos']:,}")
    print(f"  • Total Invertido:                              ${st['total_invested']:,.2f} USD")
    print(f"  • Total Cobrado:                                ${st['total_collected']:,.2f} USD")
    print(f"  • Pico Histórico de Capital (ATH):              ${st['peak_bankroll']:,.2f} USD")
    print("=" * 115)
