"""
========================================================================================
 BOT SNIPER CUANTITATIVO BRASIL (Lotto Brasil & Lotto Bicho en Paralelo)
========================================================================================
Módulo 100% independiente y segregado del bot venezolano (sniper_bot.py).
Monitorea en tiempo real los sorteos oficiales de lottobichos.com,
sincroniza el historial automáticamente, aplica los Lags circadianos preferidos (Lag 12, 24, 25...),
el filtro de exclusión de los últimos 6 turnos y emite las señales de apuesta exacta
únicamente cuando se activa el Gatillo Post-Fallo 1 (Sniper Virtual).

Incorpora:
1. Criterio de Full Kelly con Cojín de Protección No-Lineal Grossman-Zhou (MDD Floor).
2. Agente de Salud de la Estrategia con Ponderación Adaptativa de Capital (1.20x a 0.35x).
3. Monitoreo en paralelo de ambas ruletas brasileñas con persistencia en bot_state_brasil.json.
========================================================================================
"""

import argparse
import datetime
import json
import os
import sys
import time
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd
import requests

# Forzar codificación UTF-8 en Windows para evitar errores cp1252
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "bot_state_brasil.json")
API_URL = "https://lottobichos.com/sorteios/getsorteios"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}

DIAS_MAP = {
    0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves",
    4: "Viernes", 5: "Sábado", 6: "Domingo"
}

HORAS_MAP = {
    "H_08": "8:00 AM",
    "H_09": "9:00 AM",
    "H_10": "10:00 AM",
    "H_11": "11:00 AM",
    "H_12": "12:00 PM",
    "H_13": "1:00 PM",
    "H_14": "2:00 PM",
    "H_15": "3:00 PM",
    "H_16": "4:00 PM",
    "H_17": "5:00 PM",
    "H_18": "6:00 PM",
    "H_19": "7:00 PM",
}

ANIMALS_BASE = [
    'GOLFINHO', 'FLAMENCO', 'TOURO', 'LACRAIA', 'ESCORPIÃO', 'LEÃO', 'SAPO',
    'PERIQUITO', 'RATO', 'ARARA', 'TIGRE', 'GATO', 'CAVALO', 'MACACO',
    'POMBA', 'RAPOSA', 'URSO', 'PERU', 'BURRO', 'CABRA', 'PORCO',
    'GALO', 'CAMELO', 'ZEBRA', 'IGUANA', 'GALINHA', 'VACA', 'CACHORRO',
    'ABUTRE', 'ELEFANTE', 'JACARÉ', 'CAPIVARA', 'ESQUILO', 'PEIXE',
    'VEADO', 'GIRAFA', 'COBRA'
]

MAP_BRASIL = {"0": "GOLFINHO", "00": "BALEIA"}
MAP_BICHO = {"0": "GOLFINHO", "00": "BALEIA"}

for i in range(1, 37):
    num_str = f"{i:02d}"
    MAP_BRASIL[num_str] = "CORUJA" if i == 9 else ANIMALS_BASE[i]
    MAP_BICHO[num_str] = ANIMALS_BASE[i]


# Configuración cuantitativa optimizada por análisis de memoria circadiana
RULETAS_CONFIG = {
    "Lotto Brasil": {
        "lotr_code": "lottbrasil",
        "file": os.path.join(BASE_DIR, "lottobrasil_2anios.csv"),
        "lags": [12, 13, 24, 25],  # Picos circadianos: 12 (ayer misma hora), 24/25 (hace 2 días)
        "payout": 37.0,             # Payout oficial plataforma lottobichos.com
        "k": 38,
        "emoji": "🇧🇷",
        "active": True,
        "f_unit": 0.00346,          # Full Kelly unitario (0.346% por animal)
        "be_rate": 2.70,            # Break-even requerido: 1 / 37.0 = 2.70%
        "animal_map": MAP_BRASIL
    },
    "Lotto Bicho": {
        "lotr_code": "bicho",
        "file": os.path.join(BASE_DIR, "lottobicho_2anios.csv"),
        "lags": [12, 25, 13, 26],  # Picos circadianos: 12 (ayer misma hora: 4.11%), 25/26 (hace 2 días)
        "payout": 35.0,             # Payout oficial plataforma lottobichos.com
        "k": 38,
        "emoji": "🐆",
        "active": True,
        "f_unit": 0.00569,          # Full Kelly unitario (0.569% por animal)
        "be_rate": 2.86,            # Break-even requerido: 1 / 35.0 = 2.86%
        "animal_map": MAP_BICHO
    }
}


def fetch_live_brasil() -> Dict[str, List[Dict]]:
    """Descarga los resultados de hoy y ayer directamente desde el backend oficial de lottobichos.com."""
    res = {k: [] for k in RULETAS_CONFIG}
    today = datetime.date.today()
    dates_to_check = [today - datetime.timedelta(days=1), today]

    for cur_date in dates_to_check:
        d_str = cur_date.strftime("%d-%m-%Y")
        for lotto_name, cfg in RULETAS_CONFIG.items():
            lotr_code = cfg["lotr_code"]
            animal_map = cfg["animal_map"]
            try:
                r = requests.post(API_URL, data={"date": d_str, "lotr": lotr_code}, headers=HEADERS, timeout=8)
                if r.status_code == 200:
                    js = r.json()
                    if js.get("status"):
                        data = js.get("data", {})
                        key = list(data.keys())[0] if data else None
                        if key:
                            draws = data[key]
                            for h_code in sorted(HORAS_MAP.keys()):
                                val = draws.get(h_code)
                                if val and val != '--':
                                    val_clean = str(val).strip()
                                    hora_clean = HORAS_MAP[h_code]
                                    dia_semana = DIAS_MAP[cur_date.weekday()]
                                    animal_clean = animal_map.get(val_clean, "DESCONOCIDO")

                                    res[lotto_name].append({
                                        "fecha": cur_date.strftime("%Y-%m-%d"),
                                        "dia": dia_semana,
                                        "hora": hora_clean,
                                        "numero": val_clean,
                                        "animal": animal_clean,
                                        "loteria": lotto_name,
                                        "_sort_key": f"{cur_date.strftime('%Y-%m-%d')}_{h_code}"
                                    })
            except Exception as e:
                print(f" [!] Error al consultar API de {lotto_name} para {d_str}: {e}")

    return res


def load_and_sync_history(lotto_name: str, live_records: List[Dict]) -> pd.DataFrame:
    """Carga el CSV histórico y añade cualquier sorteo nuevo evitando duplicados."""
    cfg = RULETAS_CONFIG[lotto_name]
    csv_file = cfg["file"]

    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file, encoding='utf-8', dtype={'numero': str})
    else:
        df = pd.DataFrame(columns=["fecha", "dia", "hora", "numero", "animal", "loteria"])

    seen_keys = set(zip(df["fecha"], df["hora"]))
    new_rows = []
    for r in live_records:
        key = (r["fecha"], r["hora"])
        if key not in seen_keys:
            seen_keys.add(key)
            new_rows.append({k: v for k, v in r.items() if k != "_sort_key"})

    if new_rows:
        df_new = pd.DataFrame(new_rows)
        df = pd.concat([df, df_new], ignore_index=True)
        # Ordenar cronológicamente
        df["_h"] = pd.to_datetime(df["hora"], format="%I:%M %p", errors="coerce").dt.time
        df = df.sort_values(by=["fecha", "_h"]).drop(columns=["_h"]).reset_index(drop=True)
        df.to_csv(csv_file, index=False, encoding='utf-8')

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

    nums = df["numero"].astype(str).tolist()
    animals_map = dict(zip(df["numero"].astype(str), df["animal"]))
    total = len(nums)

    if total < (max_lag + 10):
        return {
            "error": "Historial insuficiente",
            "lotto": lotto_name
        }

    # Reconstruir racha virtual histórica y señales para el Agente de Salud
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

    total_signals = len(all_signals)
    total_hits = sum(all_signals)
    base_wr = (total_hits / total_signals * 100.0) if total_signals > 0 else 0.0

    # Ventana móvil de las últimas 50 señales del gatillo
    window = all_signals[-50:] if total_signals >= 50 else all_signals
    rec_trials = len(window)
    rec_hits = sum(window)
    rec_wr = (rec_hits / rec_trials * 100.0) if rec_trials > 0 else 0.0

    health_score = (rec_wr / base_wr * 100.0) if base_wr > 0 else 100.0
    be_rate = cfg["be_rate"]

    if rec_wr >= base_wr:
        h_status = "🟢 SALUD ÓPTIMA (+EV Activo)"
        diag = "Memoria circadiana en Lag 12 con ventaja estadística superior o igual al promedio."
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
        name = animals_map.get(c, cfg["animal_map"].get(c, "ANIMAL"))
        candidatos_info.append(f"[{c:>2}] {name}")

    descartados_info = []
    for c in cands_descartados:
        name = animals_map.get(c, cfg["animal_map"].get(c, "ANIMAL"))
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
        "f_unit": cfg["f_unit"],
        "be_rate": be_rate,
        "base_wr": base_wr,
        "rec_wr": rec_wr,
        "rec_trials": rec_trials,
        "rec_hits": rec_hits,
        "health_score": health_score,
        "h_status": h_status,
        "diag": diag
    }


def load_bot_state(default_bankroll: float = 1000.0) -> Dict:
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
    be_rate = st.get("be_rate", 2.80)
    health_score = st.get("health_score", 100.0)

    if rec_wr < be_rate:
        weight = 0.35
        label = "Defensivo (x0.35) [Degradada bajo Break-Even]"
    elif health_score >= 100.0:
        weight = 1.20
        label = "Prioritario (x1.20) [Salud Óptima > Promedio]"
    elif health_score >= 70.0:
        weight = 1.00
        label = "Estándar (x1.00) [Salud Normal Rentable]"
    else:
        weight = 0.70
        label = "Moderado (x0.70) [Fatiga Leve sobre Break-Even]"

    return weight, label


def display_dashboard(states: List[Dict], bankroll: float = 1000.0, peak_capital: float = 1000.0,
                      mdd_floor: float = 0.40):
    """Muestra el panel táctico en consola con Full Kelly, Grossman-Zhou y Agente de Salud."""
    peak = max(peak_capital, bankroll)
    floor = (1.0 - mdd_floor) * peak
    cushion = max(0.0, bankroll - floor)
    current_dd = ((peak - bankroll) / peak * 100.0) if peak > 0 else 0.0
    gz_multiplier = min(1.0, max(0.0, cushion / (mdd_floor * peak))) if (mdd_floor * peak) > 0 else 1.0

    print("\n" + "=" * 95)
    print(" 🇧🇷 PANEL TÁCTICO SNIPER BRASIL (Lotto Brasil & Lotto Bicho) | GROSSMAN-ZHOU + FULL KELLY")
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

        hw, hw_label = get_health_multiplier(st)

        # Apuesta Full Kelly modulada por Grossman-Zhou y Agente de Salud
        base_kelly_stake = bankroll * f_unit
        bet_per_animal = round(max(0.10, base_kelly_stake * gz_multiplier * hw), 2)
        total_cost = round(bet_per_animal * n_cands, 2)
        posible_premio = round(bet_per_animal * st["payout"], 2)
        posible_ganancia = round(posible_premio - total_cost, 2)

        print(f"\n{emoji} {lotto.upper()} (Lags Circadianos: {st['lags']} | Paga {st['payout']:.0f}x | Kelly Base: {f_unit*100:.3f}%/u)")
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
    print(" 🏥 INFORME DEL AGENTE DE SALUD (MONITOREO DE EDGE CIRCADIANO Y DEGRADACIÓN)")
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
    if optimal:
        opt_names = ", ".join([f"{o['emoji']} {o['lotto']}" for o in optimal])
        print(f"   ✅ MOTOR PRINCIPAL: Ventaja estadística robusta en: {opt_names}.")
    print("=" * 95 + "\n")


def send_telegram_alert(token: str, chat_id: str, message: str):
    """Envía un mensaje de alerta a Telegram si están configuradas las credenciales."""
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=8)
    except Exception as e:
        print(f" [!] Error al enviar alerta a Telegram: {e}")


def run_bot(check_now: bool = True, loop: bool = False, bankroll: float = 1000.0,
            mdd_floor: float = 0.40, tg_token: str = "", tg_chat: str = ""):
    print("\n[+] Iniciando Bot Cuantitativo Sniper Brasil (Lotto Brasil & Lotto Bicho)...")
    print(f"[+] Modo: Full Kelly con Colchón Grossman-Zhou (MDD Floor: {mdd_floor*100:.0f}%)")
    print(f"[+] Consultando resultados oficiales en vivo de lottobichos.com...")

    state_data = load_bot_state(default_bankroll=bankroll)
    if bankroll != 1000.0 or "bankroll" not in state_data:
        state_data["bankroll"] = bankroll
    
    current_cap = state_data["bankroll"]
    peak_cap = max(state_data.get("peak_capital", current_cap), current_cap)
    state_data["peak_capital"] = peak_cap
    save_bot_state(state_data)

    while True:
        live_data = fetch_live_brasil()
        states = []
        alert_msgs = []

        for lotto_name, cfg in RULETAS_CONFIG.items():
            if not cfg.get("active", True):
                continue
            df_sync = load_and_sync_history(lotto_name, live_data.get(lotto_name, []))
            st = evaluate_roulette_state(lotto_name, df_sync)
            states.append(st)

            if st.get("gatillo_activo") and st.get("candidatos"):
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
    parser = argparse.ArgumentParser(description="Bot Sniper Cuantitativo para Ruletas Brasileñas")
    parser.add_argument("--bankroll", type=float, default=1000.0, help="Capital actual en USD (por defecto: 1000.0)")
    parser.add_argument("--mdd_floor", type=float, default=0.40, help="Techo máximo de Drawdown para Grossman-Zhou (por defecto: 0.40 = 40%)")
    parser.add_argument("--loop", action="store_true", help="Ejecutar en modo monitor continuo (cada 4 minutos)")
    parser.add_argument("--tg_token", type=str, default="", help="Token de bot de Telegram para alertas")
    parser.add_argument("--tg_chat", type=str, default="", help="Chat ID de Telegram")

    args = parser.parse_args()
    run_bot(
        check_now=True,
        loop=args.loop,
        bankroll=args.bankroll,
        mdd_floor=args.mdd_floor,
        tg_token=args.tg_token,
        tg_chat=args.tg_chat
    )


if __name__ == "__main__":
    main()
