"""
========================================================================================
 BOT SNIPER CUANTITATIVO MULTI-RULETA (Lotto Activo, Granjita, Royal, Guacharo)
========================================================================================
Monitorea en tiempo real los resultados de TuAzar, actualiza el historial,
aplica los Lags preferidos de rebote, el filtro de exclusión de los últimos 6 turnos
y emite las señales de apuesta exacta únicamente cuando se activa el Gatillo Post-Fallo 1.
========================================================================================
"""

import argparse
import datetime
import json
import os
import sys
import time
from typing import Dict, List, Optional, Set, Tuple

import lxml.html
import pandas as pd
import requests

# Forzar codificación UTF-8 en Windows para evitar errores cp1252
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SEMANA_URL = "https://www.tuazar.com/loteria/animalitos/resultados/semana/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}

DIAS_MAP = {
    0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves",
    4: "Viernes", 5: "Sábado", 6: "Domingo"
}

# Configuración matemática optimizada por bucle algorítmico de rebote
RULETAS_CONFIG = {
    "Lotto Activo": {
        "file": os.path.join(BASE_DIR, "lotto_activo_2anios.csv"),
        "lags": [20, 18, 14],
        "payout": 30.0,
        "k": 38,
        "emoji": "🦁",
        "active": True,
        "f_unit": 0.00900,  # Full Kelly unitario (0.900% por animal)
        "be_rate": 3.33     # Break-even requerido (%)
    },
    "La Granjita": {
        "file": os.path.join(BASE_DIR, "la_granjita_2anios.csv"),
        "lags": [15, 17],
        "payout": 30.0,
        "k": 38,
        "emoji": "🐸",
        "active": True,
        "f_unit": 0.00484,  # Full Kelly unitario (0.484% por animal)
        "be_rate": 3.33
    },
    "Ruleta Royal": {
        "file": os.path.join(BASE_DIR, "ruleta_royal_2anios.csv"),
        "lags": [16, 19, 31],
        "payout": 30.0,
        "k": 37,
        "emoji": "👑",
        "active": True,
        "f_unit": 0.00826,  # Full Kelly unitario (0.826% por animal)
        "be_rate": 3.33
    },
    "Guacharo Activo": {
        "file": os.path.join(BASE_DIR, "guacharo_activo_2anios.csv"),
        "lags": [31, 41, 25, 42, 35],
        "payout": 60.0,
        "k": 77,
        "emoji": "🦇",
        "active": True,
        "f_unit": 0.00680,  # Full Kelly unitario (0.680% por animal)
        "be_rate": 1.67
    },
    "Selva Plus": {
        "file": os.path.join(BASE_DIR, "selva_plus_2anios.csv"),
        "lags": [35, 18, 36],
        "payout": 80.0,
        "k": 100,
        "emoji": "🌿",
        "active": False,  # Desactivada a petición del usuario
        "f_unit": 0.00492,  # Full Kelly unitario (0.492% por animal)
        "be_rate": 1.25
    },
    "El Guacharito Millonario": {
        "file": os.path.join(BASE_DIR, "guacharito_millonario_2anios.csv"),
        "lags": [49, 39, 42],
        "payout": 70.0,
        "k": 100,
        "emoji": "🦜",
        "active": False,  # Desactivado por defecto (-EV estructural)
        "f_unit": 0.0,
        "be_rate": 1.43
    }
}

HORARIOS_ESTANDAR = [
    "8:00 AM", "9:00 AM", "10:00 AM", "11:00 AM", "12:00 PM",
    "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM",
    "6:00 PM", "7:00 PM"
]


def parse_date_dmy(dmy_str: str) -> Optional[datetime.date]:
    try:
        parts = dmy_str.strip().split('/')
        if len(parts) == 3:
            return datetime.date(int(parts[2]), int(parts[1]), int(parts[0]))
    except Exception:
        pass
    return None


def fetch_live_semana() -> Dict[str, List[Dict]]:
    """Descarga los resultados más recientes de la semana en curso desde TuAzar."""
    res = {k: [] for k in RULETAS_CONFIG}
    try:
        r = requests.get(SEMANA_URL, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return res
        doc = lxml.html.fromstring(r.text)
        cards = doc.xpath('//div[contains(@class, "lw-card")]')

        for card in cards:
            title_el = card.xpath('.//h3[contains(@class, "lw-title")]')
            if not title_el:
                continue
            card_title = title_el[0].text_content().strip()

            # Mapeo ESTRICTO para evitar colisiones
            target_lotto = None
            if card_title == "Lotto Activo":
                target_lotto = "Lotto Activo"
            elif card_title == "Ruleta Royal":
                target_lotto = "Ruleta Royal"
            elif card_title == "La Granjita":
                target_lotto = "La Granjita"
            elif card_title in ["Guacharo Activo", "Guácharo Activo"]:
                target_lotto = "Guacharo Activo"
            elif card_title == "Selva Plus":
                target_lotto = "Selva Plus"
            elif card_title == "El Guacharito Millonario":
                target_lotto = "El Guacharito Millonario"

            if not target_lotto:
                continue

            table = card.xpath('.//table[contains(@class, "lw-table")]')
            if not table:
                continue
            table = table[0]

            day_headers = table.xpath('.//thead//th[contains(@class, "lw-day")]')
            column_dates = []
            for th in day_headers:
                day_num_el = th.xpath('.//span[contains(@class, "lw-day-num")]')
                if day_num_el:
                    column_dates.append(parse_date_dmy(day_num_el[0].text_content()))
                else:
                    column_dates.append(None)

            rows = table.xpath('.//tbody/tr')
            for row in rows:
                time_el = row.xpath('.//th[contains(@class, "lw-time")]')
                draw_time = time_el[0].text_content().strip() if time_el else ""
                cells = row.xpath('.//td')

                for dt, cell in zip(column_dates, cells):
                    if dt is None:
                        continue
                    num_el = cell.xpath('.//span[@class="lw-animal-num"]')
                    animal_el = cell.xpath('.//span[@class="lw-animal"]')
                    if num_el and animal_el:
                        num = num_el[0].text_content().strip()
                        animal = animal_el[0].text_content().strip()
                        if num and animal and num != "-":
                            # Doble candado: descartar horarios incompatibles
                            if target_lotto in ["Lotto Activo", "La Granjita", "Guacharo Activo"] and ":30" in draw_time:
                                continue
                            if target_lotto == "Ruleta Royal" and ":00" in draw_time:
                                continue

                            res[target_lotto].append({
                                "fecha": dt.strftime("%Y-%m-%d"),
                                "dia": DIAS_MAP.get(dt.weekday(), ""),
                                "hora": draw_time,
                                "numero": str(num),
                                "animal": str(animal),
                                "loteria": target_lotto
                            })
    except Exception as e:
        print(f" [!] Advertencia al conectar con TuAzar: {e}")
    return res


def load_and_sync_history(lotto_name: str, live_records: List[Dict]) -> pd.DataFrame:
    """Carga el CSV histórico y le añade cualquier sorteo nuevo de la semana."""
    csv_file = RULETAS_CONFIG[lotto_name]["file"]
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file, encoding='utf-8-sig', dtype={'numero': str})
    else:
        df = pd.DataFrame(columns=["fecha", "dia", "hora", "numero", "animal", "loteria"])

    # Fusionar con los datos en vivo evitando duplicados
    seen_keys = set(zip(df["fecha"], df["hora"]))
    new_rows = []
    for r in live_records:
        key = (r["fecha"], r["hora"])
        if key not in seen_keys:
            seen_keys.add(key)
            new_rows.append(r)

    if new_rows:
        df_new = pd.DataFrame(new_rows)
        df = pd.concat([df, df_new], ignore_index=True)
        # Ordenar y guardar
        df["_h"] = pd.to_datetime(df["hora"], format="%I:%M %p", errors="coerce").dt.time
        df = df.sort_values(by=["fecha", "_h"]).drop(columns=["_h"]).reset_index(drop=True)
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')

    return df


def evaluate_roulette_state(lotto_name: str, df: pd.DataFrame) -> Dict:
    """
    Evalúa la secuencia histórica, calcula la racha virtual del sistema
    y determina la predicción y el estado del Gatillo Post-Fallo 1 para el próximo sorteo.
    """
    cfg = RULETAS_CONFIG[lotto_name]
    lags = cfg["lags"]
    max_lag = max(lags)

    # Ordenar cronológicamente
    df["sort_key"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
    df = df.sort_values(by="sort_key").reset_index(drop=True)

    nums = df["numero"].tolist()
    animals_map = dict(zip(df["numero"], df["animal"]))
    total = len(nums)

    if total < (max_lag + 10):
        return {
            "error": "Historial insuficiente",
            "lotto": lotto_name
        }

    # Reconstruir la racha virtual histórica y señales para el Agente de Salud
    streak = 0
    all_signals = []
    for i in range(max_lag + 6, total):
        actual = nums[i]
        rec6 = set(nums[i-6:i])
        cands = list({nums[i-l] for l in lags} - rec6)
        hit = (actual in cands)
        if cands:
            if streak == 1:
                all_signals.append(hit)
            if hit:
                streak = 0
            else:
                streak += 1

    # Cálculos del Agente de Salud
    total_signals = len(all_signals)
    total_hits = sum(all_signals)
    base_wr = (total_hits / total_signals * 100.0) if total_signals > 0 else 0.0

    # Ventana móvil de las últimas 50 señales del gatillo
    window = all_signals[-50:] if total_signals >= 50 else all_signals
    rec_trials = len(window)
    rec_hits = sum(window)
    rec_wr = (rec_hits / rec_trials * 100.0) if rec_trials > 0 else 0.0

    health_score = (rec_wr / base_wr * 100.0) if base_wr > 0 else 100.0
    be_rate = cfg.get("be_rate", (1.0 / cfg["payout"]) * 100.0)

    if rec_wr >= base_wr:
        h_status = "🟢 SALUD ÓPTIMA (+EV Activo)"
        diag = "Lags con ventaja estadística superior o igual al promedio histórico."
    elif rec_wr >= be_rate:
        h_status = "🟡 SALUD NORMAL (+EV Moderado)"
        diag = "Rentable sobre Break-Even; varianza normal a corto plazo."
    else:
        h_status = "🔴 ALERTA DEGRADACIÓN (-EV Temporal)"
        diag = f"Aciertos recientes ({rec_wr:.1f}%) bajo Break-Even ({be_rate:.1f}%). Monitorear."

    ultimo_sorteo = df.iloc[-1]
    fecha_ult = ultimo_sorteo["fecha"]
    hora_ult = ultimo_sorteo["hora"]
    num_ult = ultimo_sorteo["numero"]
    animal_ult = ultimo_sorteo["animal"]

    # Calcular candidatos para el PRÓXIMO sorteo (i = total)
    rec6_actual = set(nums[-6:])
    cands_raw = [nums[-l] for l in lags]
    cands_unicos = []
    for c in cands_raw:
        if c not in cands_unicos:
            cands_unicos.append(c)

    cands_filtrados = [c for c in cands_unicos if c not in rec6_actual]
    cands_descartados = [c for c in cands_unicos if c in rec6_actual]

    gatillo_activo = (streak == 1)

    candidatos_info = []
    for c in cands_filtrados:
        name = animals_map.get(c, "ANIMAL")
        candidatos_info.append(f"[{c:>2}] {name}")

    descartados_info = []
    for c in cands_descartados:
        name = animals_map.get(c, "ANIMAL")
        descartados_info.append(f"[{c:>2}] {name} (salió en ult 6h)")

    return {
        "lotto": lotto_name,
        "emoji": cfg["emoji"],
        "payout": cfg["payout"],
        "lags": lags,
        "total_sorteos": total,
        "ultimo_resultado": f"{fecha_ult} {hora_ult} -> Nº {num_ult} ({animal_ult})",
        "racha_actual": streak,
        "gatillo_activo": gatillo_activo,
        "candidatos": candidatos_info,
        "candidatos_codigos": cands_filtrados,
        "descartados": descartados_info,
        "f_unit": cfg.get("f_unit", 0.007),
        "be_rate": be_rate,
        "base_wr": base_wr,
        "rec_wr": rec_wr,
        "rec_trials": rec_trials,
        "rec_hits": rec_hits,
        "health_score": health_score,
        "h_status": h_status,
        "diag": diag
    }


def send_telegram_alert(token: str, chat_id: str, message: str):
    """Envía un mensaje de alerta a Telegram si están configuradas las credenciales."""
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=8)
    except Exception as e:
        print(f" [!] Error al enviar alerta a Telegram: {e}")


STATE_FILE = os.path.join(BASE_DIR, "bot_state.json")

def load_bot_state(default_bankroll: float = 100.0) -> Dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "bankroll": default_bankroll,
        "peak_capital": default_bankroll,
        "losses_streak": 0
    }

def save_bot_state(state: Dict):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


def get_health_multiplier(st: Dict) -> Tuple[float, str]:
    """Calcula el multiplicador de asignación de capital según el nivel de salud/degradación."""
    rec_wr = st.get("rec_wr", 0.0)
    base_wr = st.get("base_wr", 0.0)
    be_rate = st.get("be_rate", 3.33)
    health_score = st.get("health_score", 100.0)

    if rec_wr < be_rate:
        # Enfriamiento bajo Break-Even: Escala defensiva (35% de la apuesta normal)
        weight = 0.35
        label = "Defensivo (x0.35) [Degradada bajo Break-Even]"
    elif health_score >= 100.0:
        # Salud Óptima (racha caliente superior al promedio): Asignación prioritaria (+20%)
        weight = 1.20
        label = "Prioritario (x1.20) [Salud Óptima > Promedio]"
    elif health_score >= 70.0:
        # Salud Normal rentable: Asignación estándar 100%
        weight = 1.00
        label = "Estándar (x1.00) [Salud Normal Rentable]"
    else:
        # Fatiga leve sobre Break-Even: Reducción preventiva 70%
        weight = 0.70
        label = "Moderado (x0.70) [Fatiga Leve sobre Break-Even]"

    return weight, label


def display_dashboard(states: List[Dict], bankroll: float = 100.0, peak_capital: float = 100.0,
                      mdd_floor: float = 0.40):
    """Muestra el panel de control táctico en consola con Full Kelly, Cojín GZ y Agente de Salud."""
    peak = max(peak_capital, bankroll)
    floor = (1.0 - mdd_floor) * peak
    cushion = max(0.0, bankroll - floor)
    current_dd = ((peak - bankroll) / peak * 100.0) if peak > 0 else 0.0
    gz_multiplier = min(1.0, max(0.0, cushion / (mdd_floor * peak))) if (mdd_floor * peak) > 0 else 1.0

    print("\n" + "=" * 95)
    print(" 🎯 PANEL TÁCTICO SNIPER MULTI-RULETA | FASE DEMO: FULL KELLY + COJÍN GROSSMAN-ZHOU")
    print(f"    Capital de Cuenta: ${bankroll:,.2f} USD  |  Pico Histórico (ATH): ${peak:,.2f} USD  |  Drawdown: {current_dd:.2f}%")
    print(f"    Suelo de Protección: ${floor:,.2f} USD (MDD Máx {mdd_floor*100:.0f}%) | Colchón Activo: ${cushion:,.2f} USD | Escala Kelly: {gz_multiplier*100:.1f}%")
    print("=" * 95)

    hay_disparos = False

    for st in states:
        lotto = st["lotto"]
        emoji = st["emoji"]
        gatillo = st["gatillo_activo"]
        streak = st["racha_actual"]
        cands = st["candidatos"]
        n_cands = len(cands)
        f_unit = st["f_unit"]

        # Ponderación dinámica según degradación de la estrategia
        hw, hw_label = get_health_multiplier(st)

        # Apuesta Full Kelly modulada dinámicamente por Grossman-Zhou Y por Salud
        base_kelly_stake = bankroll * f_unit
        bet_per_animal = round(max(0.10, base_kelly_stake * gz_multiplier * hw), 2)
        total_cost = round(bet_per_animal * n_cands, 2)
        posible_premio = round(bet_per_animal * st["payout"], 2)
        posible_ganancia = round(posible_premio - total_cost, 2)

        print(f"\n{emoji} {lotto.upper()} (Lags analizados: {st['lags']} | Paga {st['payout']:.0f}x | Full Kelly Base: {f_unit*100:.3f}%/u)")
        print(f"   • Último resultado registrado: {st['ultimo_resultado']}")
        print(f"   • Racha de fallos del sistema: {streak} sorteo(s)")

        if gatillo and n_cands > 0:
            hay_disparos = True
            print("   " + "🚨" * 16)
            print("   >>> ¡GATILLO TÁCTICO ACTIVO! (DISPARAR APUESTA AHORA) <<<")
            print("   " + "🚨" * 16)
            print(f"   • Animales a JUGAR ({n_cands} opciones):")
            for c in cands:
                print(f"       👉 {c}")
            if st["descartados"]:
                print(f"   • Excluidos por filtro reciente: {', '.join(st['descartados'])}")
            print(f"   • Gestión de Capital Adaptativa:")
            print(f"       - Ponderación de Salud: {hw_label}")
            print(f"       - Apostar: ${bet_per_animal:.2f} USD a cada uno (Costo total: ${total_cost:.2f} USD)")
            print(f"       - Si acierta cobra: ${posible_premio:.2f} USD (Ganancia neta: +${posible_ganancia:.2f} USD)")
        else:
            print("   ⏳ ESTADO: EN ESPERA (NO APOSTAR EN ESTE SORTEO)")
            if streak == 0:
                print("      -> Razón: El sistema viene de ganar en el sorteo previo. Esperando el próximo fallo.")
            elif streak > 1:
                print(f"      -> Razón: Lleva {streak} fallos seguidos. Fuera de la ventana de alta probabilidad.")
            elif n_cands == 0:
                print("      -> Razón: Todos los candidatos fueron descartados por el filtro de 6 horas.")

    print("\n" + "=" * 95)
    print(" 🏥 INFORME DEL AGENTE DE SALUD DE LA ESTRATEGIA (MONITOREO DE EDGE Y DEGRADACIÓN DE LAGS)")
    print("=" * 95)
    print(f"{'Ruleta':<24} | {'WR Base (2a)':<12} | {'WR Reciente (50s)':<17} | {'Break-Even':<10} | {'Salud Edge':<10} | {'Estado Diagnóstico'}")
    print("-" * 95)

    for st in states:
        wr_b = f"{st['base_wr']:.2f}%"
        wr_r = f"{st['rec_wr']:.2f}% ({st['rec_hits']}/{st['rec_trials']})"
        be = f"{st['be_rate']:.2f}%"
        hlth = f"{st['health_score']:.1f}%"
        print(f"{st['emoji']} {st['lotto']:<21} | {wr_b:<12} | {wr_r:<17} | {be:<10} | {hlth:<10} | {st['h_status']}")

    print("-" * 95)
    print(" 💡 Resumen Semanal del Agente de Salud:")
    degraded = [s for s in states if "ALERTA" in s["h_status"]]
    optimal = [s for s in states if "ÓPTIMA" in s["h_status"]]
    if degraded:
        deg_names = ", ".join([f"{d['emoji']} {d['lotto']}" for d in degraded])
        print(f"   ⚠️ ATENCIÓN: Se detecta enfriamiento temporal en: {deg_names}.")
        print("      -> Recomendación: Si la tendencia persiste durante 2 semanas, ejecutar el bucle de optimización de lags.")
    if optimal:
        opt_names = ", ".join([f"{o['emoji']} {o['lotto']}" for o in optimal])
        print(f"   ✅ MOTOR PRINCIPAL: Ventaja estadística robusta y saludable en: {opt_names}.")
    print("=" * 95 + "\n")


def run_bot(check_now: bool = True, loop: bool = False, bankroll: float = 1000.0,
            mdd_floor: float = 0.40, tg_token: str = "", tg_chat: str = "", include_all: bool = False):
    print("\n[+] Iniciando Bot Cuantitativo Multi-Ruleta...")
    print(f"[+] Modo: Full Kelly Demo con Colchón Grossman-Zhou (MDD Floor: {mdd_floor*100:.0f}%)")
    print(f"[+] Consultando resultados en vivo de TuAzar...")

    state_data = load_bot_state(default_bankroll=bankroll)
    if bankroll != 1000.0 or "bankroll" not in state_data:
        state_data["bankroll"] = bankroll
    
    current_cap = state_data["bankroll"]
    peak_cap = max(state_data.get("peak_capital", current_cap), current_cap)
    state_data["peak_capital"] = peak_cap
    save_bot_state(state_data)

    while True:
        live_data = fetch_live_semana()
        states = []
        alert_msgs = []

        for lotto_name, cfg in RULETAS_CONFIG.items():
            if not cfg.get("active", True) and not include_all:
                continue
            df_sync = load_and_sync_history(lotto_name, live_data.get(lotto_name, []))
            st = evaluate_roulette_state(lotto_name, df_sync)
            states.append(st)

            if st.get("gatillo_activo") and st.get("candidatos"):
                # Cálculo de apuesta
                peak = max(peak_cap, current_cap)
                floor = (1.0 - mdd_floor) * peak
                cushion = max(0.0, current_cap - floor)
                gz_mult = min(1.0, max(0.0, cushion / (mdd_floor * peak))) if (mdd_floor * peak) > 0 else 1.0
                hw, hw_label = get_health_multiplier(st)
                bet_amt = round(max(0.10, current_cap * st["f_unit"] * gz_mult * hw), 2)
                cands_str = "\n".join([f"  • {c}" for c in st["candidatos"]])
                msg = (
                    f"🚨 *SEÑAL DE APUESTA ACTIVA: {st['lotto']}* 🚨\n\n"
                    f"Próximo sorteo. Apostar ${bet_amt:.2f} USD por animal ({hw_label}):\n"
                    f"{cands_str}\n\n"
                    f"Pago: {st['payout']:.0f}x | Full Kelly Modulado GZ + Salud | Racha Post-Fallo 1"
                )
                alert_msgs.append(msg)

        display_dashboard(states, current_cap, peak_cap, mdd_floor)

        if alert_msgs and tg_token and tg_chat:
            for m in alert_msgs:
                send_telegram_alert(tg_token, tg_chat, m)

        if not loop:
            break

        print("[i] Modo monitor activo. Próxima actualización en 4 minutos (o Ctrl+C para salir)...")
        time.sleep(240)


def main():
    parser = argparse.ArgumentParser(description="Bot Sniper Cuantitativo para Ruletas de Animalitos")
    parser.add_argument("--bankroll", type=float, default=1000.0, help="Capital actual en USD (por defecto: 1000.0)")
    parser.add_argument("--mdd_floor", type=float, default=0.40, help="Techo máximo de Drawdown para Grossman-Zhou (por defecto: 0.40 = 40%)")
    parser.add_argument("--loop", action="store_true", help="Ejecutar en modo monitor continuo (cada 4 minutos)")
    parser.add_argument("--include_all", action="store_true", help="Incluir también ruletas con EV negativo como Guacharito Millonario")
    parser.add_argument("--tg_token", type=str, default="", help="Token de bot de Telegram para alertas")
    parser.add_argument("--tg_chat", type=str, default="", help="Chat ID de Telegram")

    args = parser.parse_args()
    run_bot(
        check_now=True,
        loop=args.loop,
        bankroll=args.bankroll,
        mdd_floor=args.mdd_floor,
        tg_token=args.tg_token,
        tg_chat=args.tg_chat,
        include_all=args.include_all
    )


if __name__ == "__main__":
    main()
