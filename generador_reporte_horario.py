"""
========================================================================================
 GENERADOR DE REPORTE VISUAL CRONOLÓGICO INTRADÍA (CARTERA 7 RULETAS)
========================================================================================
Reconstruye y formatea el desarrollo cronológico hora por hora de todos los sorteos
del día, detallando:
 1. Hora del sorteo y Ruleta
 2. Número y animal salido oficial
 3. Condición de la estrategia (Racha previa, Gatillo Sniper, Zona de Rebote)
 4. ¿Hubo o no disparo?
 5. Números/animales seleccionados (si hubo disparo)
 6. Resultado y variación de capital (PnL)
 7. Saldo acumulado en banca tras el evento
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
    DEFAULT_BANKROLL,
)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
    except Exception:
        pass


def parse_time_for_sort(time_str: str) -> datetime.time:
    """Convierte cadenas como '8:05 AM', '12:30 PM' en objeto datetime.time para ordenar exactamente."""
    try:
        dt = datetime.datetime.strptime(time_str.strip(), "%I:%M %p")
        return dt.time()
    except Exception:
        return datetime.time(23, 59)


def get_timeline_for_date(target_date: str = None) -> List[Dict]:
    if target_date is None:
        target_date = datetime.date.today().strftime("%Y-%m-%d")

    # Cargar ledger oficial
    ledger_records = {}
    if os.path.exists(LEDGER_FILE):
        ldf = pd.read_csv(LEDGER_FILE)
        ldf_target = ldf[ldf["fecha"].astype(str) == target_date]
        for _, row in ldf_target.iterrows():
            key = (str(row["ruleta"]).strip(), str(row["hora"]).strip())
            ledger_records[key] = row.to_dict()

    events = []

    # Recorrer cada una de las 7 ruletas activas
    for r_name, cfg in RULETAS_CONFIG.items():
        if not cfg.get("active", False):
            continue

        fpath = cfg["file"]
        if not os.path.exists(fpath):
            continue

        df = pd.read_csv(fpath, dtype={"numero": str})
        df["numero"] = df["numero"].astype(str).str.strip()
        df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        df = df.sort_values(by="sort_dt").reset_index(drop=True)

        nums = df["numero"].tolist()
        dates = df["fecha"].tolist() if "fecha" in df.columns else [""] * len(nums)
        lags = cfg["lags"]
        target_streaks = cfg.get("target_streaks", [1])
        rec_w = cfg.get("rec_w", 6)
        use_anti_cluster = cfg.get("anti_clustering", False)
        min_idx = max(lags) + max(rec_w, 8)

        # Mapeo a nombre de animalito
        num_to_animal = {}
        for _, row in df.iterrows():
            num_to_animal[str(row["numero"])] = str(row["animal"])

        # Reconstruir estado sorteo a sorteo
        streak = 0
        seen_today = set()
        prev_date = None
        prev_was_repeat = False

        for i in range(min_idx, len(nums)):
            actual = nums[i]
            d = str(dates[i]).strip()
            row_dict = df.iloc[i].to_dict()
            hora = str(row_dict.get("hora", "")).strip()

            if d != prev_date:
                prev_date = d
                seen_today = set()
                prev_was_repeat = False

            rec_set = set(nums[i-rec_w:i])
            cands = sorted(list({nums[i-l] for l in lags if i >= l} - rec_set))
            is_repeat_now = (actual in seen_today)
            skip_shot = bool(use_anti_cluster and prev_was_repeat)

            # Estado antes de este sorteo
            streak_before = streak
            is_trigger = (streak_before in target_streaks) and bool(cands) and (not skip_shot)

            # Verificar si este sorteo pertenece al target_date
            if d == target_date:
                # Comprobar si hay registro en el ledger
                ledger_match = ledger_records.get((r_name, hora))

                cands_str_list = [f"#{c} {num_to_animal.get(c, '')}".strip() for c in cands]
                cands_display = ", ".join(cands_str_list) if cands_str_list else "Sin selección"

                anim_actual = num_to_animal.get(actual, row_dict.get("animal", ""))
                salido_str = f"#{actual} {anim_actual}".strip()

                event_info = {
                    "fecha": d,
                    "hora": hora,
                    "sort_time": parse_time_for_sort(hora),
                    "ruleta": r_name,
                    "emoji": cfg.get("emoji", "🎯"),
                    "salido": salido_str,
                    "salido_num": actual,
                    "salido_anim": anim_actual,
                    "racha_previa": streak_before,
                    "candidatos": cands_display,
                    "cands_count": len(cands),
                    "es_gatillo": is_trigger,
                    "skip_anti_cluster": skip_shot,
                    "hubo_disparo": bool(ledger_match is not None),
                    "ledger_info": ledger_match,
                }
                events.append(event_info)

            # Actualizar racha para el siguiente sorteo
            if cands and not skip_shot:
                hit = (actual in cands)
                if hit:
                    streak = 0
                else:
                    streak += 1
            elif cands and skip_shot:
                hit = (actual in cands)
                streak = 0 if hit else streak + 1

            seen_today.add(actual)
            prev_was_repeat = is_repeat_now

    # Ordenar todos los eventos cronológicamente por hora del día
    events = sorted(events, key=lambda x: (x["sort_time"], x["ruleta"]))
    return events


def render_markdown_visual_timeline(events: List[Dict], initial_bankroll: float = 241.89) -> str:
    """Genera la tabla visual y narrativa del desarrollo del día."""
    lines = []
    lines.append("### ⏱️ Desarrollo Visual Cronológico del Día (Hora por Hora)")
    lines.append("")
    lines.append("| Hora | Ruleta | Salido Oficial | Condición Estrategia | ¿Disparo? | Números Seleccionados | Resultado / PnL | Saldo en Banca |")
    lines.append("| :---: | :--- | :---: | :--- | :---: | :--- | :---: | :---: |")

    current_saldo = initial_bankroll

    for ev in events:
        hora = ev["hora"]
        ruleta = f"{ev['emoji']} {ev['ruleta']}"
        salido = f"**{ev['salido']}**"
        racha = ev["racha_previa"]

        # Condición descriptiva
        if ev["es_gatillo"]:
            cond = f"🎯 **GATILLO Racha {racha}**"
        elif ev["skip_anti_cluster"]:
            cond = f"🛡️ Bloqueo AntiCluster"
        elif racha == 0:
            cond = f"💤 Espera Fallo (R0)"
        else:
            cond = f"⏳ Racha {racha} (Fuera Zona)"

        if ev["hubo_disparo"]:
            leg = ev["ledger_info"]
            disparo_icon = "💥 **SÍ**"
            cands = f"`{leg.get('candidatos', ev['candidatos'])}`"
            pnl_val = float(leg.get("pnl", 0.0))
            current_saldo = float(leg.get("saldo", current_saldo))
            if pnl_val > 0:
                res_str = f"🟢 **+${pnl_val:.2f}**"
            else:
                res_str = f"🔴 **-${abs(pnl_val):.2f}**"
            saldo_str = f"**${current_saldo:.2f} USD**"
        else:
            disparo_icon = "⚪ No"
            cands = "---"
            res_str = "---"
            saldo_str = f"${current_saldo:.2f} USD"

        lines.append(f"| {hora} | {ruleta} | {salido} | {cond} | {disparo_icon} | {cands} | {res_str} | {saldo_str} |")

    return "\n".join(lines)


if __name__ == "__main__":
    # Determinar saldo inicial del día
    from bot_nuevas_ruletas import load_state
    state = load_state()
    current_b = state.get("bankroll", 265.11)
    timeline = get_timeline_for_date()
    # Si hubo operaciones hoy, el saldo inicial es el del inicio de hoy, sino es el actual
    md_output = render_markdown_visual_timeline(timeline, initial_bankroll=current_b)
    print(md_output)
