"""
========================================================================================
 BOT SNIPER MULTI-RULETA AUTÓNOMO (NUEVAS RULETAS: Gatazo, Mega Animal 40, Monje)
========================================================================================
Sistema de trading algorítmico cuantitativo para loterías de animalitos.
Opera en tiempo real aplicando:
 1. Selección por Lags óptimos de autocorrelación comprobada.
 2. Filtro estricto de recencia intra-día (exclusión de las últimas 6 horas).
 3. Gatillo Sniper de dispersión de racha: Apuesta únicamente tras Racha 1 (1 fallo previo).
 4. Gestión de capital paramétrica: $1.00 USD fijo o Full Kelly fraccional.
 5. Registro contable granular en ledger CSV y diario visual Markdown.
========================================================================================
"""

import argparse
import datetime
import json
import os
import sys
import re
import time
from typing import Dict, List, Optional, Set, Tuple

import lxml.html
import pandas as pd
import requests

from config import (
    BASE_DIR,
    BASE_TUAZAR_URL,
    DEFAULT_BANKROLL,
    DIARIO_FILE,
    DIAS_MAP,
    FATIGUE_DISCOUNT_MULTIPLIER,
    FIXED_STAKE_UNIT,
    HEADERS,
    LEDGER_FILE,
    MDD_FLOOR,
    MIN_BET,
    NEUTRAL_MULTIPLIER,
    PEAK_DECAY_WEEKS,
    QUARANTINE_MISSES,
    REBOUND_BOOST_MULTIPLIER,
    RULETAS_CONFIG,
    SEMANA_URL,
    SIZING_MODEL,
    SMART_INVESTMENT_ENABLED,
    STATE_FILE,
    TARGET_MDD,
    WEEKLY_CIRCUIT_BREAKER_PCT,
    WEEKLY_CYCLE_DAYS,
    WEEKLY_KELLY_MULTIPLIER,
    WEEKLY_RESET_ENABLED,
)
from live_auditor_engine import LIVE_AUDITOR

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
    except Exception:
        pass


def clean_animal_name(name: str) -> str:
    if not isinstance(name, str):
        return ""
    name = name.strip()
    exact_map = {
        "AGUILA": "ÁGUILA", "ALACRAN": "ALACRÁN", "CAIMAN": "CAIMÁN",
        "CIEMPIES": "CIEMPIÉS", "DELFIN": "DELFÍN", "LEON": "LEÓN",
        "RATON": "RATÓN", "TIBURON": "TIBURÓN", "TUCAN": "TUCÁN",
        "BUFALO": "BÚFALO", "CHUGUIRE": "CHIGÜIRE", "PUERCOESPIN": "PUERCOESPÍN",
        "CAMALEON": "CAMALEÓN", "GAVILAN": "GAVILÁN", "HIPOPOTAMO": "HIPOPÓTAMO",
        "ARANA": "ARAÑA",
    }
    return exact_map.get(name, name)


def parse_date_dmy(dmy_str: str) -> Optional[datetime.date]:
    try:
        parts = dmy_str.strip().split('/')
        if len(parts) == 3:
            return datetime.date(int(parts[2]), int(parts[1]), int(parts[0]))
    except Exception:
        pass
    return None


def load_state() -> Dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                st = json.load(f)
                # Asegurar presencia de campos de Grossman-Zhou
                if "peak_bankroll" not in st:
                    st["peak_bankroll"] = max(st.get("bankroll", DEFAULT_BANKROLL), DEFAULT_BANKROLL)
                if "mdd_floor" not in st:
                    st["mdd_floor"] = MDD_FLOOR
                if "min_bet" not in st:
                    st["min_bet"] = MIN_BET
                if "sizing_model" not in st:
                    st["sizing_model"] = SIZING_MODEL
                return st
        except Exception as e:
            print(f"⚠️ Error leyendo {STATE_FILE}: {e}. Intentando recuperar respaldo...")
            backup_file = STATE_FILE + ".bak"
            if os.path.exists(backup_file):
                try:
                    with open(backup_file, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    pass
    # Estado inicial por defecto solo si no existe archivo previo válido
    initial = {
        "bankroll": DEFAULT_BANKROLL,
        "initial_bankroll": DEFAULT_BANKROLL,
        "peak_bankroll": DEFAULT_BANKROLL,
        "mdd_floor": MDD_FLOOR,
        "min_bet": MIN_BET,
        "sizing_model": SIZING_MODEL,
        "created_at": datetime.datetime.now().isoformat(),
        "last_updated": datetime.datetime.now().isoformat(),
        "cycle_start_time": datetime.datetime.now().isoformat(),
        "cycle_start_bankroll": DEFAULT_BANKROLL,
        "cycle_number": 1,
        "cycle_pnl": 0.0,
        "weekly_fixed_stakes": {},
        "total_invested": 0.0,
        "total_collected": 0.0,
        "total_pnl": 0.0,
        "wins": 0,
        "losses": 0,
        "streaks": {k: 0 for k in RULETAS_CONFIG.keys()},
        "last_seen_draw": {k: "" for k in RULETAS_CONFIG.keys()},
        "active_bets": {}  # sorteo_key: {ruleta, hora, fecha, cands, stake_unit, cost}
    }
    save_state(initial)
    return initial


def manage_weekly_cycle(state: Dict) -> Dict:
    """Gestiona el ciclo de reinicio de 7 días, decay de ATH, amortiguación funcional y circuit breaker."""
    now = datetime.datetime.now()
    bankroll = state.get("bankroll", DEFAULT_BANKROLL)

    if "cycle_start_time" not in state or not state["cycle_start_time"]:
        state["cycle_start_time"] = now.isoformat()
        state["cycle_start_bankroll"] = bankroll
        state["cycle_number"] = 1
        state["cycle_pnl"] = 0.0

    try:
        start_time = datetime.datetime.fromisoformat(state["cycle_start_time"])
    except Exception:
        start_time = now
        state["cycle_start_time"] = now.isoformat()

    elapsed_days = (now - start_time).total_seconds() / 86400.0

    # Desvanecimiento del ATH para evitar parálisis de High-Water Mark
    decay_factor = (0.5 ** (1.0 / PEAK_DECAY_WEEKS)) if PEAK_DECAY_WEEKS > 0 else 1.0
    peak = state.get("peak_bankroll", bankroll)

    # Si se cumplieron los 7 días (o múltiplos), cerrar ciclo y consolidar nuevo saldo base
    if elapsed_days >= WEEKLY_CYCLE_DAYS:
        cycle_num = state.get("cycle_number", 1)
        pnl_cycle = bankroll - state.get("cycle_start_bankroll", bankroll)
        base_b = state.get("cycle_start_bankroll", bankroll)
        pct_cycle = (pnl_cycle / base_b * 100.0) if base_b > 0 else 0.0
        pnl_sign = "+" if pnl_cycle >= 0 else ""
        print("\n" + "=" * 95)
        print(f"🎉 ¡CULMINACIÓN DEL CICLO SEMANAL N° {cycle_num}! (7 Días Completos)")
        print(f"   Saldo Base Anterior: ${base_b:,.2f} USD -> Saldo Consolidado: ${bankroll:,.2f} USD")
        print(f"   Resultado Neto Semanal: {pnl_sign}${pnl_cycle:,.2f} USD ({pnl_sign}{pct_cycle:.2f}%)")
        print(f"   🚀 Iniciando Ciclo N° {cycle_num + 1} con nuevo capital base de: ${bankroll:,.2f} USD")
        print("=" * 95 + "\n")

        state["cycle_number"] = cycle_num + 1
        state["cycle_start_time"] = now.isoformat()
        if SIZING_MODEL == "fixed_stake_with_weekly_withdrawals":
            if pnl_cycle > 0:
                withdrawn = pnl_cycle
                state["total_withdrawn"] = round(state.get("total_withdrawn", 0.0) + withdrawn, 2)
                bankroll = DEFAULT_BANKROLL
                state["bankroll"] = bankroll
                state["cycle_start_bankroll"] = DEFAULT_BANKROLL
                print(f"   💰 GANANCIAS RETIRADAS: +${withdrawn:,.2f} USD a la cartera. Saldo en mesa reiniciado a ${DEFAULT_BANKROLL:.2f} USD.")
            else:
                state["cycle_start_bankroll"] = bankroll
        else:
            state["cycle_start_bankroll"] = bankroll
        state["cycle_pnl"] = 0.0
        elapsed_days = 0.0
        # Aplicar decay al inicio del nuevo ciclo
        peak = max(bankroll, peak * decay_factor)
        state["peak_bankroll"] = peak

    cycle_base = state.get("cycle_start_bankroll", bankroll)
    curr_dd = (peak - cycle_base) / peak if peak > 0 else 0.0

    # Amortiguación continua de Kelly
    damping = max(0.15, 1.0 - (curr_dd / TARGET_MDD)) if TARGET_MDD > 0 else 1.0
    effective_kelly = WEEKLY_KELLY_MULTIPLIER * damping
    state["effective_kelly"] = round(effective_kelly, 4)
    state["damping"] = round(damping, 4)

    # Calcular apuestas unitarias fijas para la semana (Optimizado)
    fixed_stakes = {}
    for r_name, cfg in RULETAS_CONFIG.items():
        if not cfg.get("active", True):
            continue
        if SIZING_MODEL == "fixed_stake_with_weekly_withdrawals":
            stk = FIXED_STAKE_UNIT
        else:
            f_u = cfg.get("f_unit", 0.008)
            stk = round(max(MIN_BET, cycle_base * f_u * effective_kelly), 2)
        fixed_stakes[r_name] = stk

    state["weekly_fixed_stakes"] = fixed_stakes
    state["cycle_elapsed_days"] = elapsed_days
    return state


def calcular_peso_agente(r_name: str, streak: int, trigger_miss: int) -> Tuple[int, str]:
    """
    Agente evaluador por ruleta: devuelve (peso_1_10, label_corto).
    3 dimensiones: posición en racha, factor de pago, momento de rebote trigger.
    Basado en WR condicional empírico del ledger histórico.
    """
    cfg = RULETAS_CONFIG.get(r_name, {})
    payout = cfg.get("payout", 30)
    wr_optimos: list = cfg.get("wr_optimos", [1])

    # Dim 1 — Posición en racha (0-4 pts)
    if streak in wr_optimos:
        s_racha = 4
    elif streak <= 1:
        s_racha = 3
    elif streak <= 5:
        s_racha = 2
    elif streak <= 20:
        s_racha = 1
    else:
        s_racha = 0

    # Dim 2 — Factor de pago (1-3 pts)
    s_pago = 3 if payout >= 60 else 2

    # Dim 3 — Momento de rebote por trigger misses (0-3 pts)
    if 1 <= trigger_miss <= 3:
        s_trigger = 3
    elif trigger_miss == 0:
        s_trigger = 1
    elif trigger_miss <= 8:
        s_trigger = 2
    else:
        s_trigger = 0

    peso = max(1, min(10, s_racha + s_pago + s_trigger))
    label = f"P:{peso}/10"
    return peso, label


def get_rebound_momentum_multiplier(trigger_misses: int) -> Tuple[float, str]:
    """Determina el multiplicador de inversión inteligente según la condición óptima del patrón."""
    if not SMART_INVESTMENT_ENABLED:
        return 1.00, "Inversión Estándar (1.00x)"
    if 1 <= trigger_misses <= 3:
        return REBOUND_BOOST_MULTIPLIER, f"🔥 Zona Dulce Rebote ({REBOUND_BOOST_MULTIPLIER:.2f}x Kelly)"
    elif trigger_misses == 0:
        return FATIGUE_DISCOUNT_MULTIPLIER, f"🛡️ Zona Fatigada ({FATIGUE_DISCOUNT_MULTIPLIER:.2f}x Kelly)"
    else:
        return NEUTRAL_MULTIPLIER, f"⚖️ Neutral ({NEUTRAL_MULTIPLIER:.2f}x Kelly)"


def calculate_stake_grossman_zhou(
    bankroll: float,
    peak: float,
    f_unit: float,
    min_bet: float = MIN_BET,
    mdd_floor: float = MDD_FLOOR,
    smart_multiplier: float = 1.0
) -> Tuple[float, float, float]:
    """Calcula la apuesta unitaria por animal aplicando Full Kelly amortiguado por el colchón Grossman-Zhou y modulación inteligente."""
    peak = max(peak, bankroll)
    floor = (1.0 - mdd_floor) * peak
    cushion = max(0.0, bankroll - floor)
    gz_multiplier = min(1.0, max(0.0, cushion / (mdd_floor * peak))) if (mdd_floor * peak) > 0 else 1.0
    base_stake = bankroll * f_unit
    unit_bet = round(max(min_bet, base_stake * gz_multiplier * smart_multiplier), 2)
    return unit_bet, cushion, gz_multiplier


def save_state(state: Dict):
    state["last_updated"] = datetime.datetime.now().isoformat()
    tmp_file = STATE_FILE + ".tmp"
    bak_file = STATE_FILE + ".bak"
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        # Si ya existe STATE_FILE, crear copia de respaldo previa
        if os.path.exists(STATE_FILE):
            try:
                import shutil
                shutil.copyfile(STATE_FILE, bak_file)
            except Exception:
                pass
        # Reemplazo atómico POSIX/Windows
        os.replace(tmp_file, STATE_FILE)
        # Espejo automático hacia app_movil/static para sincronización móvil instantánea
        try:
            static_dir = os.path.join(ROOT_DIR, "app_movil", "static")
            if os.path.exists(static_dir):
                import shutil
                shutil.copy2(STATE_FILE, os.path.join(static_dir, "state_nuevas_ruletas.json"))
        except Exception:
            pass
    except Exception as e:
        print(f"⚠️ Error en escritura atómica de estado: {e}")
        # Fallback de emergencia
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)


def fetch_tuazar_today_results() -> Dict[str, List[Dict]]:
    """Descarga la página principal del día de TuAzar y extrae los resultados oficiales en tiempo real."""
    extracted = {k: [] for k in RULETAS_CONFIG.keys()}
    try:
        resp = requests.get(BASE_TUAZAR_URL, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return extracted
        doc = lxml.html.fromstring(resp.text)
    except Exception as e:
        print(f"⚠️ Error conectando con TuAzar (hoy): {e}")
        return extracted

    today_date = None
    maintitle = doc.xpath('//h1[contains(@class, "maintitle")]')
    if maintitle:
        m_txt = maintitle[0].text_content()
        match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', m_txt)
        if match:
            day, month, year = match.groups()
            today_date = datetime.date(int(year), int(month), int(day))
    if not today_date:
        today_date = datetime.date.today()
    date_str = today_date.strftime("%Y-%m-%d")
    dia_str = DIAS_MAP[today_date.weekday()]

    cards = doc.xpath('//div[contains(@class, "lc-card")]')
    for c in cards:
        t = c.xpath('.//h3[contains(@class, "lc-title")]')
        if not t:
            continue
        title = t[0].text_content().strip()
        matched = None
        for r_name, cfg in RULETAS_CONFIG.items():
            card_title = cfg["card_title"].lower()
            t_lower = title.lower()
            if card_title in t_lower:
                if "lotto activo" in t_lower and "rd" in t_lower and "rd" not in card_title:
                    continue
                matched = r_name
                break
        if not matched:
            continue

        tiles = c.xpath('.//div[contains(concat(" ", normalize-space(@class), " "), " lc-tile ")]')
        for tile in tiles:
            cls = tile.get("class", "")
            if "lc-tile--empty" in cls:
                continue
            time_el = tile.xpath('.//div[contains(@class, "lc-tile-time")]')
            num_el = tile.xpath('.//span[contains(@class, "lc-tile-num")]')
            anim_el = tile.xpath('.//span[contains(@class, "lc-tile-animal")]')
            if not time_el or not num_el:
                continue
            hora = time_el[0].text_content().strip()
            num = num_el[0].text_content().strip()
            anim = anim_el[0].text_content().strip() if anim_el else ""
            if anim.startswith(num):
                anim = anim[len(num):].strip()
            if num.isdigit() or num in ["0", "00"]:
                extracted[matched].append({
                    "fecha": date_str,
                    "dia": dia_str,
                    "hora": hora,
                    "numero": str(num),
                    "animal": clean_animal_name(anim),
                    "loteria": matched
                })
    return extracted


def fetch_tuazar_week_results() -> Dict[str, List[Dict]]:
    """Descarga la página de la semana de TuAzar y extrae los resultados oficiales de días anteriores."""
    extracted = {k: [] for k in RULETAS_CONFIG.keys()}
    try:
        resp = requests.get(SEMANA_URL, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            return extracted
        doc = lxml.html.fromstring(resp.text)
    except Exception as e:
        print(f"⚠️ Error conectando con TuAzar (semana): {e}")
        return extracted

    cards = doc.xpath('//div[contains(@class, "lw-card")]')
    for card in cards:
        title_el = card.xpath('.//h3[contains(@class, "lw-title")]')
        if not title_el:
            continue
        card_title = title_el[0].text_content().strip()
        matched_r_name = None
        for r_name, r_cfg in RULETAS_CONFIG.items():
            if r_cfg["card_title"].lower() in card_title.lower():
                if "lotto activo" in card_title.lower() and "rd" in card_title.lower() and "rd" not in r_cfg["card_title"].lower():
                    continue
                matched_r_name = r_name
                break
        if not matched_r_name:
            continue

        day_ths = card.xpath('.//table//thead//th[contains(@class, "lw-day")]')
        col_dates = []
        for th in day_ths:
            span_num = th.xpath('.//span[contains(@class, "lw-day-num")]')
            if span_num:
                d_str = span_num[0].text_content().strip()
                col_dates.append(parse_date_dmy(d_str))
            else:
                col_dates.append(None)

        rows = card.xpath('.//table//tbody//tr')
        for row in rows:
            time_th = row.xpath('.//th[contains(@class, "lw-time")]')
            if not time_th:
                continue
            hora = time_th[0].text_content().strip()

            tds = row.xpath('.//td')
            for col_idx, td in enumerate(tds):
                if col_idx >= len(col_dates):
                    continue
                dt_obj = col_dates[col_idx]
                if not dt_obj:
                    continue

                num_el = td.xpath('.//span[@class="lw-animal-num"]')
                anim_el = td.xpath('.//span[@class="lw-animal"]')
                if num_el:
                    numero_str = num_el[0].text_content().strip()
                    animal_str = anim_el[0].text_content().strip().upper() if anim_el else ""
                    if animal_str.startswith(numero_str):
                        animal_str = animal_str[len(numero_str):].strip()
                    if numero_str.isdigit() or numero_str in ["0", "00"]:
                        extracted[matched_r_name].append({
                            "fecha": dt_obj.strftime("%Y-%m-%d"),
                            "dia": DIAS_MAP[dt_obj.weekday()],
                            "hora": hora,
                            "numero": str(numero_str),
                            "animal": clean_animal_name(animal_str),
                            "loteria": matched_r_name
                        })
    return extracted


def fetch_live_results() -> Dict[str, List[Dict]]:
    """Combina los resultados históricos de la semana y los sorteos en tiempo real del día."""
    data_week = fetch_tuazar_week_results()
    data_today = fetch_tuazar_today_results()
    # Guardar en static para sincronización directa de la PWA móvil
    try:
        static_json = os.path.join(BASE_DIR, "app_movil", "static", "tuazar_today.json")
        with open(static_json, "w", encoding="utf-8") as _f_json:
            json.dump(data_today, _f_json, ensure_ascii=False, indent=2)
    except Exception as _e_json:
        pass
    combined = {k: [] for k in RULETAS_CONFIG.keys()}
    for k in combined.keys():
        combined[k].extend(data_week.get(k, []))
        combined[k].extend(data_today.get(k, []))
    return combined


def update_local_csvs(live_data: Dict[str, List[Dict]]) -> Dict[str, int]:
    """Sincroniza los nuevos sorteos en los CSV locales para mantener la continuidad temporal."""
    new_counts = {}
    for r_name, items in live_data.items():
        if r_name not in RULETAS_CONFIG or not RULETAS_CONFIG[r_name].get("active", False):
            continue
        if not items:
            new_counts[r_name] = 0
            continue
        cfg = RULETAS_CONFIG[r_name]
        fpath = cfg["file"]

        if os.path.exists(fpath):
            df_old = pd.read_csv(fpath, dtype={"numero": str})
            df_old["numero"] = df_old["numero"].astype(str).str.strip()
        else:
            df_old = pd.DataFrame(columns=["fecha", "dia", "hora", "numero", "animal", "loteria"])

        df_new = pd.DataFrame(items)
        df_new["numero"] = df_new["numero"].astype(str).str.strip()

        combined = pd.concat([df_old, df_new], ignore_index=True)
        # Quitar duplicados por fecha y hora
        combined = combined.drop_duplicates(subset=["fecha", "hora"], keep="last")
        combined["sort_dt"] = pd.to_datetime(combined["fecha"] + " " + combined["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        combined = combined.sort_values(by="sort_dt").reset_index(drop=True)
        combined = combined.drop(columns=["sort_dt"])

        diff = len(combined) - len(df_old)
        new_counts[r_name] = max(0, diff)
        os.makedirs(os.path.dirname(os.path.abspath(fpath)), exist_ok=True)
        combined.to_csv(fpath, index=False, encoding="utf-8")

        # Exportar live_radar.json para la PWA móvil en cada pasada de actualización
    try:
        from app_movil.server_zero_dep import get_current_streaks, RULETAS
        live_radar = {}
        for r_name in RULETAS:
            st, miss, info = get_current_streaks(r_name)
            cfg = RULETAS[r_name]
            target = cfg.get('target_streaks', [1])
            is_act = (st in target) and not info.get('is_anti_blocked', False) and len(info.get('cands', [])) > 0
            live_radar[r_name] = {
                'title': cfg['title'],
                'emoji': cfg['emoji'],
                'payout': cfg['payout'],
                'target_streaks': target,
                'racha': st,
                'misses': miss,
                'is_active': is_act,
                'candidatos': info.get('cands', []),
                'ultimo_str': info.get('last_str', '')
            }
        radar_path = os.path.join(BASE_DIR, 'app_movil', 'static', 'live_radar.json')
        with open(radar_path, 'w', encoding='utf-8') as _rf:
            json.dump(live_radar, _rf, ensure_ascii=False, indent=2)

        sync_today_ledger_json()
    except Exception as _e_rad:
        pass

    return new_counts


def get_history_series(r_name: str) -> Tuple[List[str], pd.DataFrame]:
    cfg = RULETAS_CONFIG[r_name]
    df = pd.read_csv(cfg["file"], dtype={"numero": str})
    df["numero"] = df["numero"].astype(str).str.strip()
    df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
    df = df.sort_values(by="sort_dt").reset_index(drop=True)
    return df["numero"].tolist(), df


def calculate_current_streak_and_misses(r_name: str) -> Tuple[int, int]:
    """Calcula la racha actual desde el último acierto y los fallos consecutivos del gatillo sniper."""
    nums, df = get_history_series(r_name)
    cfg = RULETAS_CONFIG[r_name]
    lags = cfg["lags"]
    target_streaks = cfg.get("target_streaks", [1])
    rec_w = cfg.get("rec_w", 6)
    use_anti_cluster = cfg.get("anti_clustering", False)
    min_idx = max(lags) + max(rec_w, 8)

    streak = 0
    trigger_misses = 0
    seen_today = set()
    prev_date = None
    prev_was_repeat = False
    dates = df["fecha"].tolist() if "fecha" in df.columns else [""] * len(nums)

    for i in range(min_idx, len(nums)):
        actual = nums[i]
        d = dates[i]
        if d != prev_date:
            prev_date = d
            seen_today = set()
            prev_was_repeat = False

        rec_set = set(nums[i-rec_w:i])
        cands = list(({nums[i-l] for l in lags if i >= l} - rec_set) - set(cfg.get("blacklist", [])))

        is_repeat_now = (actual in seen_today)
        skip_shot = bool(use_anti_cluster and prev_was_repeat)

        if cands and not skip_shot:
            hit = (actual in cands)
            if streak in target_streaks:
                if hit:
                    trigger_misses = 0
                else:
                    trigger_misses += 1
            if hit:
                streak = 0
            else:
                streak += 1
        elif cands and skip_shot:
            hit = (actual in cands)
            streak = 0 if hit else streak + 1
            if streak in target_streaks:
                trigger_misses += 1

        seen_today.add(actual)
        prev_was_repeat = is_repeat_now

    return streak, trigger_misses


def calculate_current_streak(r_name: str) -> int:
    """Calcula la racha actual exacta de la ruleta desde el último sorteo jugado."""
    streak, _ = calculate_current_streak_and_misses(r_name)
    return streak


def generate_upcoming_candidates(r_name: str) -> Dict:
    nums, df = get_history_series(r_name)
    cfg = RULETAS_CONFIG[r_name]
    lags = cfg["lags"]
    rec_w = cfg.get("rec_w", 6)
    use_anti_cluster = cfg.get("anti_clustering", False)
    blacklist = set(cfg.get("blacklist", []))
    markov_snipers = cfg.get("markov_snipers", {})
    
    if len(nums) < max(lags) + max(rec_w, 8):
        return {"error": "Historial insuficiente"}

    rec_set = set(nums[-rec_w:])
    raw_lags = [nums[-l] for l in lags if l <= len(nums)]
    cands_lag = sorted(list((set(raw_lags) - rec_set) - blacklist))
    
    # Comprobar si el sorteo más reciente fue una repetición intradía
    is_anti_cluster_blocked = False
    if use_anti_cluster and len(df) >= 2:
        last_date = str(df.iloc[-1].get("fecha", "")).strip()
        day_draws = df[df["fecha"] == last_date]["numero"].tolist()
        if len(day_draws) >= 2:
            last_num_today = day_draws[-1]
            earlier_today = day_draws[:-1]
            if last_num_today in earlier_today:
                is_anti_cluster_blocked = True

    # Comprobar Canal B (Hiper-Markov Mono-Animal Sniper)
    last_num = str(nums[-1]).strip()
    markov_target = markov_snipers.get(last_num)
    is_markov_active = bool(markov_target is not None and markov_target not in rec_set and markov_target not in blacklist)

    # Comprobar Canal C (Hiper-Espejo Táctico)
    mirror_pairs = cfg.get("mirror_pairs", {})
    mirror_target = mirror_pairs.get(last_num)
    is_mirror_active = bool(mirror_target is not None and mirror_target not in rec_set and mirror_target not in blacklist)

    # Mapeo a nombre de animalito
    num_to_animal = {}
    for _, row in df.iterrows():
        num_to_animal[str(row["numero"])] = row["animal"]

    if is_markov_active:
        cands = [markov_target]
        channel_type = "MARKOV_SNIPER"
    elif is_mirror_active and not cands_lag:
        cands = [mirror_target]
        channel_type = "ESPEJO_SNIPER"
    else:
        cands = cands_lag if not is_anti_cluster_blocked else []
        channel_type = "LAG_SNIPER"

    cands_detail = [{"numero": c, "animal": num_to_animal.get(c, "DESCONOCIDO")} for c in cands]
    last_draw = df.iloc[-1].to_dict()
    last_num = str(last_draw.get("numero", "")).strip()
    last_anim = str(last_draw.get("animal", "")).strip()
    last_hora = str(last_draw.get("hora", "")).strip()
    last_fecha = str(last_draw.get("fecha", "")).strip()
    last_salido_str = f"#{last_num} {last_anim} ({last_hora})"

    return {
        "ruleta": r_name,
        "emoji": cfg["emoji"],
        "payout": cfg["payout"],
        "channel_type": channel_type,
        "is_markov_active": is_markov_active,
        "total_cands": len(cands),
        "candidates": cands_detail,
        "is_anti_cluster_blocked": (is_anti_cluster_blocked if not is_markov_active else False),
        "rec_w": rec_w,
        "rec_excluded": list(rec_set),
        "blacklist": list(blacklist),
        "last_num": last_num,
        "last_anim": last_anim,
        "last_hora": last_hora,
        "last_fecha": last_fecha,
        "last_salido_str": last_salido_str,
        "last_draw": f"{last_fecha} {last_hora} -> #{last_num} {last_anim}"
    }


def sync_today_ledger_json():
    try:
        if os.path.exists(LEDGER_FILE):
            _df_led = pd.read_csv(LEDGER_FILE)
            _today_str = datetime.date.today().strftime('%Y-%m-%d')
            _df_tod = _df_led[_df_led['fecha'] == _today_str]
            _ledger_ops = []
            for _, _row in _df_tod.iterrows():
                _ledger_ops.append({
                    'hora': _row.get('hora', ''),
                    'ruleta': _row.get('ruleta', ''),
                    'candidatos': str(_row.get('candidatos', '')),
                    'resultado': str(_row.get('resultado', '')),
                    'condicion': str(_row.get('condicion', '')),
                    'total_bet': float(_row.get('total_bet', 0)),
                    'cobrado': float(_row.get('cobrado', 0)),
                    'pnl': float(_row.get('pnl', 0)),
                    'saldo': float(_row.get('saldo', 0))
                })
            _led_path = os.path.join(BASE_DIR, 'app_movil', 'static', 'today_ledger.json')
            with open(_led_path, 'w', encoding='utf-8') as _lf:
                json.dump(_ledger_ops, _lf, ensure_ascii=False, indent=2)
    except Exception as _e_led:
        pass


def record_to_ledger(event: Dict):
    cols = [
        "fecha", "hora", "ruleta", "candidatos", "cands_count", "zona_patron",
        "smart_mult", "stake_unit", "total_bet", "resultado", "condicion",
        "cobrado", "pnl", "saldo", "peak", "drawdown_pct"
    ]
    row = {c: event.get(c, "") for c in cols}
    file_exists = os.path.exists(LEDGER_FILE) and os.path.getsize(LEDGER_FILE) > 0
    df_row = pd.DataFrame([row], columns=cols)
    df_row.to_csv(LEDGER_FILE, mode="a", header=not file_exists, index=False, encoding="utf-8")
    # Espejo automático hacia app_movil/static para sincronización móvil instantánea
    try:
        static_dir = os.path.join(ROOT_DIR, "app_movil", "static")
        if os.path.exists(static_dir):
            import shutil
            shutil.copy2(LEDGER_FILE, os.path.join(static_dir, "ledger_nuevas_ruletas.csv"))
    except Exception:
        pass
    sync_today_ledger_json()


def append_to_markdown_journal(event: Dict, state: Dict):
    """Actualiza el diario visual Markdown diario_nuevas_ruletas.md."""
    file_exists = os.path.exists(DIARIO_FILE)
    header_needed = not file_exists or os.path.getsize(DIARIO_FILE) == 0

    mode = "a" if not header_needed else "w"
    with open(DIARIO_FILE, mode, encoding="utf-8") as f:
        if header_needed:
            f.write("# 📓 Diario de Operaciones en Vivo: Nuevas Ruletas (Gatazo, Mega Animal, Monje)\n\n")
            f.write("> **Ubicación:** `C:\\Users\\victo\\nuevas_ruletas\\`  \n")
            f.write(f"> **Fecha de Inicio:** {datetime.datetime.now().strftime('%Y-%m-%d')}  \n")
            f.write("> **Estrategia:** Gatillo Sniper Racha 1 (Post-Fallo) con Filtro de Recencia 6h.  \n\n")
            f.write("## 📜 Registro Granular de Disparos y Resultados\n\n")
            f.write("| Timestamp | Ruleta | Sorteo | Animales Apostados | Salido Oficial | Resultado | Invertido ($) | Cobrado ($) | PnL Disparo | Bankroll Actual |\n")
            f.write("| :--- | :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")

        badge = "🟢 GANADA" if event["hit"] else "🔴 PERDIDA"
        pnl_str = f"{'+' if event['pnl']>=0 else ''}${event['pnl']:.2f}"
        f.write(f"| {event['timestamp']} | {event['ruleta']} | {event['hora']} | `{event['candidatos']}` | **#{event['salido_num']} {event['salido_anim']}** | {badge} | ${event['inv']:.2f} | ${event['cob']:.2f} | **{pnl_str}** | **${state['bankroll']:.2f}** |\n")


def check_and_update(verbose: bool = True) -> Dict:
    state = load_state()
    state = manage_weekly_cycle(state)
    bankroll = state.get("bankroll", DEFAULT_BANKROLL)
    peak = max(state.get("peak_bankroll", bankroll), bankroll)
    state["peak_bankroll"] = peak

    cycle_num = state.get("cycle_number", 1)
    cycle_base = state.get("cycle_start_bankroll", bankroll)
    cycle_pnl = bankroll - cycle_base
    cycle_pct = (cycle_pnl / cycle_base * 100.0) if cycle_base > 0 else 0.0
    elapsed_days = state.get("cycle_elapsed_days", 0.0)
    current_day = min(7, int(elapsed_days) + 1)
    days_left = max(0, 7 - int(elapsed_days))
    current_dd = ((peak - bankroll) / peak * 100.0) if peak > 0 else 0.0

    # Control de Riesgo Institucional: Circuit Breaker y Damping
    cb_limit_cash = -cycle_base * WEEKLY_CIRCUIT_BREAKER_PCT
    circuit_breaker_active = bool(cycle_pnl <= cb_limit_cash)
    eff_kelly = state.get("effective_kelly", WEEKLY_KELLY_MULTIPLIER)
    damping = state.get("damping", 1.0)

    total_withdrawn = state.get("total_withdrawn", 0.0)
    patrimonio_total = bankroll + total_withdrawn

    if verbose:
        print("=" * 115)
        print(" 🎯 PANEL TÁCTICO SNIPER (7 RULETAS) | MODELO: $1.00 FIJO CON RETIRO SEMANAL DE GANANCIAS")
        print(f"    Hora Actual: {datetime.datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')} | Saldo en Mesa: ${bankroll:,.2f} USD | Ganancias Retiradas: ${total_withdrawn:,.2f} USD | Patrimonio Total: ${patrimonio_total:,.2f} USD")
        print(f"    🗓️  Ciclo Semanal N° {cycle_num}: Día {current_day} de 7 (Restan {days_left} días) | Base Semanal: ${cycle_base:,.2f} USD")
        print(f"    📈 PnL Semana en Curso: {'+' if cycle_pnl>=0 else ''}${cycle_pnl:,.2f} USD ({'+' if cycle_pnl>=0 else ''}{cycle_pct:.2f}%) | Apuesta: $1.00 USD fijo por animal")
        if circuit_breaker_active:
            print("    ⚠️  ¡CIRCUIT BREAKER SEMANAL ACTIVADO! (Pérdida en el ciclo >= 15%). Disparos pausados para blindar capital.")
        print("=" * 115)

    # 1. Descargar resultados recientes de TuAzar (Semana + Hoy en tiempo real)
    if verbose:
        print("📡 Consultando resultados oficiales en vivo de TuAzar (Semana + Hoy en tiempo real)...")
    live_data = fetch_live_results()
    new_counts = update_local_csvs(live_data)

    for r_name, count in new_counts.items():
        if count > 0 and verbose:
            print(f"  📥 {r_name}: {count} nuevos sorteos sincronizados en el historial local.")

    # 1.1 Motor de Recuperación y Liquidación Determinista tras Cortes de Energía
    if "pending_bets" not in state:
        state["pending_bets"] = {}
    if "last_processed_draw" not in state:
        state["last_processed_draw"] = {}

    for r_name, cfg in RULETAS_CONFIG.items():
        if not cfg.get("active", True):
            continue
        nums, df = get_history_series(r_name)
        if df.empty:
            continue

        last_proc_str = state["last_processed_draw"].get(r_name, "")
        if not last_proc_str:
            state["last_processed_draw"][r_name] = f"{df.iloc[-1]['fecha']} {df.iloc[-1]['hora']}"
            continue

        last_proc_dt = pd.to_datetime(last_proc_str, format="%Y-%m-%d %I:%M %p", errors="coerce")
        new_draws = df[df["sort_dt"] > last_proc_dt].copy()

        if new_draws.empty:
            continue

        if verbose and len(new_draws) > 1:
            print(f"  ⚡ RECUPERACIÓN TRAS CORTE ({r_name}): Procesando {len(new_draws)} sorteos ocurridos durante la desconexión...")

        for _, res_draw in new_draws.iterrows():
            salido_num = str(res_draw["numero"]).strip()
            salido_anim = str(res_draw["animal"]).strip()
            fecha_res = str(res_draw["fecha"]).strip()
            hora_res = str(res_draw["hora"]).strip()
            curr_draw_str = f"{fecha_res} {hora_res}"

            has_pending = (r_name in state["pending_bets"])

            if has_pending:
                bet = state["pending_bets"][r_name]
                cands = bet["candidatos"]
                cands_str = bet["candidatos_str"]
                cost = bet["total_stake"]
                stake_unit = bet["stake_unit"]
                payout = bet["payout"]
                smart_label = bet.get("smart_label", "Estándar")
                cands_count = bet.get("total_cands", len(cands))
                del state["pending_bets"][r_name]
            else:
                rec_w = cfg.get("rec_w", 6)
                use_anti_cluster = cfg.get("anti_clustering", False)
                draw_idx_matches = df.index[df["sort_dt"] == res_draw["sort_dt"]]
                if len(draw_idx_matches) == 0 or draw_idx_matches[0] < max(cfg["lags"]) + max(rec_w, 8):
                    state["last_processed_draw"][r_name] = curr_draw_str
                    continue
                d_idx = draw_idx_matches[0]
                past_nums = nums[:d_idx]
                r_streak = state["streaks"].get(r_name, 0)
                r_misses = state["trigger_misses"].get(r_name, 0)
                is_quar = bool(QUARANTINE_MISSES > 0 and r_misses >= QUARANTINE_MISSES)
                
                # Check anti-cluster blocking for recovery
                is_recov_blocked = False
                if use_anti_cluster and d_idx >= 2:
                    recov_date = str(df.iloc[d_idx-1].get("fecha", "")).strip()
                    d_sub = df.iloc[:d_idx]
                    d_day = d_sub[d_sub["fecha"] == recov_date]["numero"].tolist()
                    if len(d_day) >= 2 and d_day[-1] in d_day[:-1]:
                        is_recov_blocked = True

                if r_streak in cfg.get("target_streaks", [1]) and not is_quar and not circuit_breaker_active and not is_recov_blocked:
                    rec_set = set(past_nums[-rec_w:])
                    raw_cands = [past_nums[-l] for l in cfg["lags"] if l <= len(past_nums)]
                    c_list = sorted(list((set(raw_cands) - rec_set) - set(cfg.get("blacklist", []))))
                    if c_list:
                        num_to_anim = {str(row["numero"]): row["animal"] for _, row in df.iloc[:d_idx].iterrows()}
                        cands = c_list
                        p_agente, p_label = calcular_peso_agente(r_name, r_streak, r_misses)
                        cands_str = ", ".join([f"#{c} {num_to_anim.get(c, '')} [{p_label}]" for c in c_list])
                        cands_count = len(c_list)
                        if SIZING_MODEL == "fixed_stake_with_weekly_withdrawals":
                            stake_unit = FIXED_STAKE_UNIT
                        else:
                            f_u = cfg.get("f_unit", 0.008)
                            stake_unit = round(max(MIN_BET, cycle_base * f_u * eff_kelly), 2)
                        cost = round(cands_count * stake_unit, 2)
                        payout = cfg["payout"]
                        smart_label = f"[RECUPERADO TRAS CORTE] Kelly {eff_kelly:.2f}x"
                        has_pending = True
                    else:
                        has_pending = False
                else:
                    has_pending = False

            if has_pending:
                hit = (salido_num in cands)
                cobrado = round(stake_unit * payout, 2) if hit else 0.0
                pnl = round(cobrado - cost, 2)

                bankroll = round(bankroll + pnl, 2)
                state["bankroll"] = bankroll
                state["peak_bankroll"] = max(state["peak_bankroll"], bankroll)
                state["total_invested"] = round(state.get("total_invested", 0.0) + cost, 2)
                state["total_collected"] = round(state.get("total_collected", 0.0) + cobrado, 2)
                state["total_pnl"] = round(state.get("total_pnl", 0.0) + pnl, 2)
                if hit:
                    state["wins"] = state.get("wins", 0) + 1
                    state["streaks"][r_name] = 0
                    state["trigger_misses"][r_name] = 0
                else:
                    state["losses"] = state.get("losses", 0) + 1
                    state["streaks"][r_name] = state["streaks"].get(r_name, 0) + 1
                    state["trigger_misses"][r_name] = state["trigger_misses"].get(r_name, 0) + 1

                dd_pct = ((state["peak_bankroll"] - bankroll) / state["peak_bankroll"] * 100.0) if state["peak_bankroll"] > 0 else 0.0
                event = {
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
                    "fecha": fecha_res,
                    "hora": hora_res,
                    "ruleta": r_name,
                    "candidatos": cands_str,
                    "cands_count": cands_count,
                    "zona_patron": smart_label,
                    "smart_mult": 1.0,
                    "stake_unit": stake_unit,
                    "total_bet": cost,
                    "resultado": f"[{salido_num}] {salido_anim}",
                    "condicion": "🟢 GANADA" if hit else "🔴 PERDIDA",
                    "cobrado": cobrado,
                    "pnl": pnl,
                    "saldo": bankroll,
                    "peak": state["peak_bankroll"],
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

                if verbose:
                    print("\n" + "#" * 115)
                    if hit:
                        print(f"  🎉🎉 ¡DISPARO GANADOR RECUPERADO/CONFIRMADO EN {r_name}! (+${pnl:.2f} USD)")
                    else:
                        print(f"  🔴 DISPARO NO ACERTADO EN {r_name} (-${cost:.2f} USD)")
                    print(f"     • Sorteo: {fecha_res} {hora_res} -> #{salido_num} {salido_anim}")
                    print(f"     • Jugados: {cands_str} ({cands_count} fichas a ${stake_unit:.2f})")
                    print(f"     • PnL: {'+' if pnl>=0 else ''}${pnl:.2f} USD | Saldo: ${bankroll:,.2f} USD")
                    print("#" * 115 + "\n")
            else:
                # Mantener sincronizada la racha sorteo a sorteo durante desconexiones para no perder gatillos
                rec_w = cfg.get("rec_w", 6)
                past_nums = nums[:d_idx]
                rec_set = set(past_nums[-rec_w:])
                raw_cands = [past_nums[-l] for l in cfg["lags"] if l <= len(past_nums)]
                c_list = sorted(list((set(raw_cands) - rec_set) - set(cfg.get("blacklist", []))))
                if c_list and not is_recov_blocked:
                    hit_pattern = (salido_num in c_list)
                    if r_streak in cfg.get("target_streaks", [1]):
                        if hit_pattern:
                            state["trigger_misses"][r_name] = 0
                        else:
                            state["trigger_misses"][r_name] = state["trigger_misses"].get(r_name, 0) + 1
                    if hit_pattern:
                        state["streaks"][r_name] = 0
                    else:
                        state["streaks"][r_name] = state["streaks"].get(r_name, 0) + 1
                elif c_list and is_recov_blocked:
                    hit_pattern = (salido_num in c_list)
                    state["streaks"][r_name] = 0 if hit_pattern else (state["streaks"].get(r_name, 0) + 1)

            state["last_processed_draw"][r_name] = curr_draw_str

    # 2. Actualizar rachas de cada ruleta y preparar radar táctico
    active_signals = []
    all_radar_items = []
    if "trigger_misses" not in state:
        state["trigger_misses"] = {}

    for r_name, cfg in RULETAS_CONFIG.items():
        if not cfg["active"]:
            continue
        streak, trigger_misses = calculate_current_streak_and_misses(r_name)
        state["streaks"][r_name] = streak
        state["trigger_misses"][r_name] = trigger_misses

        cands_info = generate_upcoming_candidates(r_name)
        cost_fichas = cands_info["total_cands"]
        
        # Inversión Inteligente: Modulación Rebound Momentum
        smart_mult, smart_label = get_rebound_momentum_multiplier(trigger_misses)
        
        # Dimensionamiento de Apuesta: $1.00 USD Fijo o Kelly Optimizado
        f_unit = cfg.get("f_unit", 0.008)
        if SIZING_MODEL == "fixed_stake_with_weekly_withdrawals":
            stake_unit = FIXED_STAKE_UNIT
        else:
            stake_unit = state.get("weekly_fixed_stakes", {}).get(
                r_name,
                round(max(MIN_BET, cycle_base * f_unit * eff_kelly), 2)
            )
        total_stake = round(cost_fichas * stake_unit, 2)
        posible_premio = round(stake_unit * cfg["payout"], 2)

        # Calcular peso del agente evaluador para esta ruleta en este momento
        peso_agente, peso_label = calcular_peso_agente(r_name, streak, trigger_misses)
        peso_stars = "★" * min(peso_agente, 5) + "☆" * (5 - min(peso_agente, 5))
        cands_formatted = ", ".join(
            [f"#{c['numero']} {c['animal']} [{peso_label}]" for c in cands_info["candidates"]]
        )

        # Verificación de Cuarentena Preventiva (Rachas Frías Prolongadas)
        is_quarantined = bool(QUARANTINE_MISSES > 0 and trigger_misses >= QUARANTINE_MISSES)

        # Cálculo de fallos faltantes para entrar
        target_streaks = cfg.get("target_streaks", [1])
        min_target = min(target_streaks)
        max_target = max(target_streaks)

        if is_quarantined:
            fallos_restantes = -2
            conteo_str = f"🧊 Cuarentena Preventiva ({trigger_misses})"
            urgencia = 4
            badge = f"🧊 Cuarentena ({trigger_misses} fallos)"
        elif streak in target_streaks:
            fallos_restantes = 0
            conteo_str = "🚨 ¡DISPARAR AHORA! (0)"
            urgencia = 1
            badge = f"🔥 Racha {streak} (Objetivo)"
        elif streak < min_target:
            fallos_restantes = min_target - streak
            conteo_str = f"⚠️ FALTA {fallos_restantes} FALLO" if fallos_restantes == 1 else f"⚠️ FALTAN {fallos_restantes} FALLOS"
            urgencia = 2
            badge = "🟢 Racha 0 (Post-Win)" if streak == 0 else f"🟡 Racha {streak}"
        else:
            fallos_restantes = -1
            conteo_str = f"💤 Espera reinicio ({streak})"
            urgencia = 3
            badge = f"🟡 Racha {streak} Fallos"

        r_card = {
            "ruleta": f"{cfg['emoji']} {r_name}",
            "name": r_name,
            "emoji": cfg["emoji"],
            "racha": streak,
            "badge": badge,
            "urgencia": urgencia,
            "fallos_restantes": fallos_restantes,
            "conteo_str": conteo_str,
            "target_streaks": target_streaks,
            "trigger_misses": trigger_misses,
            "smart_mult": smart_mult,
            "smart_label": smart_label,
            "payout": cfg["payout"],
            "total_cands": cost_fichas,
            "candidates_str": cands_formatted,
            "stake_unit": stake_unit,
            "total_stake": total_stake,
            "posible_premio": posible_premio,
            "f_unit": f_unit,
            "gz_mult": damping,
            "peso_agente": peso_agente,
            "peso_label": peso_label,
            "peso_stars": peso_stars,
            "last_salido_str": cands_info.get("last_salido_str", "---"),
            "last_draw": cands_info.get("last_draw", "")
        }

        # Consulta de auditoría de deriva y estado de régimen para todas las ruletas activas
        nums_r, df_r = get_history_series(r_name)
        drift_info = LIVE_AUDITOR.regime_cache.get(r_name)
        if not drift_info and not df_r.empty:
            drift_info = LIVE_AUDITOR.audit_betting_opportunity(
                r_name, cands_info["candidates"], stake_unit, df_r, cfg, state, trigger_misses
            )["drift_audit"]
        r_card["drift_info"] = drift_info

        is_markov_op = cands_info.get("is_markov_active", False)
        is_mirror_op = (cands_info.get("channel_type") == "ESPEJO_SNIPER")
        if (streak in target_streaks) or is_markov_op or is_mirror_op:
            if is_markov_op:
                r_card["badge"] = "⚡ Markov Sniper"
                r_card["conteo_str"] = "🚨 ¡DISPARAR MARKOV! (1)"
                r_card["urgencia"] = 1
            elif is_mirror_op:
                r_card["badge"] = "🪞 Espejo Sniper"
                r_card["conteo_str"] = "🚨 ¡DISPARAR ESPEJO! (1)"
                r_card["urgencia"] = 1
            if circuit_breaker_active:
                r_card["badge"] = "⚠️ Circuit Breaker"
                r_card["conteo_str"] = "⚠️ Pausado por Límite Semanal"
            elif is_quarantined and not is_markov_op and not is_mirror_op:
                r_card["badge"] = f"🧊 Cuarentena ({trigger_misses} fallos)"
                r_card["conteo_str"] = "🧊 Omitido por Racha Fría"
            elif cands_info.get("is_anti_cluster_blocked", False) and not is_markov_op and not is_mirror_op:
                r_card["badge"] = "🛡️ AntiCluster Activo"
                r_card["conteo_str"] = "🛡️ Bloqueado por Repetición"
            else:
                # AUDITORÍA EN VIVO PREVIA A LA COMPRA (Multi-Agent Live Audit)
                audit_res = LIVE_AUDITOR.audit_betting_opportunity(
                    r_name=r_name,
                    candidates=cands_info["candidates"],
                    base_stake_unit=stake_unit,
                    df=df_r,
                    cfg=cfg,
                    state=state,
                    trigger_misses=trigger_misses
                )
                r_card["audit_res"] = audit_res
                r_card["smart_label"] = f"{smart_label} | {audit_res['strength_audit']['badge']}"

                if audit_res["order_status"] == "INHIBIDA_POR_AUDITOR":
                    r_card["badge"] = "🛑 Inhibido por Auditor"
                    r_card["conteo_str"] = "🛑 Ruptura/Fatiga Severa"
                    if r_name in state["pending_bets"]:
                        del state["pending_bets"][r_name]
                else:
                    if SIZING_MODEL == "fixed_stake_with_weekly_withdrawals":
                        final_stake = FIXED_STAKE_UNIT
                        r_card["stake_unit"] = final_stake
                        r_card["total_stake"] = round(cost_fichas * final_stake, 2)
                        r_card["posible_premio"] = round(final_stake * cfg["payout"], 2)
                    else:
                        final_stake = audit_res["final_stake_unit"]
                        r_card["stake_unit"] = final_stake
                        r_card["total_stake"] = audit_res["total_cost"]
                        r_card["posible_premio"] = audit_res["posible_premio"]
                    active_signals.append(r_card)
                    if r_name not in state["pending_bets"]:
                        state["pending_bets"][r_name] = {
                            "ruleta": r_name,
                            "candidatos": [str(c["numero"]) for c in cands_info["candidates"]],
                            "candidatos_str": cands_formatted,
                            "total_cands": cost_fichas,
                            "stake_unit": final_stake,
                            "total_stake": r_card["total_stake"],
                            "posible_premio": r_card["posible_premio"],
                            "payout": cfg["payout"],
                            "smart_label": r_card["smart_label"],
                            "audit_verdict": audit_res["strength_audit"]["verdict"],
                            "audit_multiplier": audit_res["strength_audit"]["capital_multiplier"],
                            "last_fecha": cands_info["last_fecha"],
                            "last_hora": cands_info["last_hora"],
                            "last_salido_str": cands_info["last_salido_str"],
                            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
                        }
        all_radar_items.append(r_card)

    # Guardar estado actualizado
    save_state(state)

    # Mostrar informe táctico en consola (PowerShell compatible)
    if verbose:
        # 1. PANEL DE ENTRADA INMEDIATA
        print("\n" + "=" * 115)
        print(" 🎯 SEÑALES DE ENTRADA INMINENTE (LUEGO DEL FALLO - COMPRA ACTIVA):")
        print("=" * 115)
        if active_signals:
            for s in active_signals:
                print(f" 🚨 ¡ENTRADA INMINENTE ACTIVADA! -> {s['ruleta']} (Payout: {s['payout']:.0f}x)")
                print(f"    • ESTADO:                   {s['conteo_str']} | Racha Actual: {s['racha']}")
                print(f"    • Último Sorteo Salido:     {s['last_salido_str']}")
                print(f"    • Condición del Patrón:     {s['smart_label']}")
                print(f"    • ANIMALES A COMPRAR:       {s['candidates_str']} ({s['total_cands']} animales)")
                print(f"    • MONTO PARA CADA UNO:      ${s['stake_unit']:.2f} USD c/u")
                print(f"    • 💰 MONTO TOTAL A COMPRAR: ${s['total_stake']:.2f} USD")
                print(f"    • 🏆 PREMIO POTENCIAL:      ${s['posible_premio']:.2f} USD")
                print(f"    • Historial Oficial:        {s['last_draw']}")
                print("-" * 115)
        else:
            print("  ⚪ NINGUNA ENTRADA INMINENTE EN ESTE MOMENTO.")
            print("     (Los números, nombres y montos a comprar solo se revelan tras ocurrir el fallo del gatillo).")

        # 2. RADAR DE MONITOREO Y CONTEO DE FALLOS (CON ÚLTIMO SALIDO Y HORA)
        all_radar_items.sort(key=lambda x: (x["urgencia"], x["racha"]))
        print("\n" + "=" * 165)
        print(" 📡 RADAR DE MONITOREO TÁCTICO (ESTADO, CONTEO DE FALLOS Y ÚLTIMO SALIDO CON HORA):")
        print("=" * 165)
        headers = f" {'RULETA':<19} | {'ESTADO ACTUAL':<19} | {'FALLOS QUE FALTAN':<22} | {'ÚLTIMO SALIDO (HORA)':<26} | {'ANIMALES A COMPRAR':<26} | {'MONTO C/U':<11} | {'TOTAL':<11} | {'PREMIO':<11} | {'CONDICIÓN PATRÓN'}"
        print(headers)
        print("-" * 165)

        for item in all_radar_items:
            if item["fallos_restantes"] == 0:
                # Entrada Inminente: Revelar números, nombres y montos exactos
                c_text = item['candidates_str']
                if len(c_text) > 24:
                    c_text = c_text[:22] + ".."
                c_display = f"{c_text} ({item['total_cands']})"
                apuesta_str = f"${item['stake_unit']:.2f}"
                total_str = f"💰 ${item['total_stake']:.2f}"
                premio_str = f"🏆 ${item['posible_premio']:.2f}"
            else:
                # En espera de fallo: Mantener oculto para no confundir
                c_display = "🔒 Oculto (Tras fallo)"
                apuesta_str = "---"
                total_str = "---"
                premio_str = "---"

            u_salido = item.get("last_salido_str", "---")
            if len(u_salido) > 25:
                u_salido = u_salido[:23] + ".."

            row = f" {item['ruleta']:<19} | {item['badge']:<19} | {item['conteo_str']:<22} | {u_salido:<26} | {c_display:<26} | {apuesta_str:<11} | {total_str:<11} | {premio_str:<11} | {item['smart_label']}"
            print(row)

        print("=" * 165 + "\n")

        # 3. PANEL DE AGENTES AUDITORES EN VIVO (FORTALEZA DE PATRÓN, DERIVA Y DIRECCIÓN)
        print("=" * 165)
        print(" 🛡️ PANEL DE AUDITORÍA MULTI-AGENTE EN VIVO (FORTALEZA DE PATRÓN, DERIVA Y DIRECCIÓN):")
        print("=" * 165)
        headers_audit = f" {'RULETA':<19} | {'FORTALEZA AUDITADA':<25} | {'Z-SCORE':<8} | {'ESTADO RÉGIMEN':<24} | {'HACIA DÓNDE SE DIRIGE EL PATRÓN / ACCIÓN':<65} | {'MULT'}"
        print(headers_audit)
        print("-" * 165)
        for item in all_radar_items:
            drift = item.get("drift_info") or {}
            reg_st = drift.get("regime_status", "ESTABLE")
            direc = drift.get("drift_direction", "Alineado con lags oficiales")
            rec = drift.get("action_recommendation", "Mantener estrategia")

            audit_res = item.get("audit_res")
            if audit_res:
                st_badge = audit_res["strength_audit"]["badge"]
                z_sc = f"{audit_res['strength_audit']['z_score']:+.2f}"
                mult_s = f"{audit_res['strength_audit']['capital_multiplier']:.2f}x"
            else:
                st_badge = "⚖️ Base (En Monitoreo)"
                z_sc = "---"
                mult_s = "1.00x"

            summary_dir = f"{direc} -> {rec}"
            if len(summary_dir) > 63:
                summary_dir = summary_dir[:61] + ".."

            row_a = f" {item['ruleta']:<19} | {st_badge:<25} | {z_sc:<8} | {reg_st:<24} | {summary_dir:<65} | {mult_s}"
            print(row_a)
        print("=" * 165 + "\n")

        # 4. AGENTE SUPERVISOR DE REPETICIÓN Y PATRONES EMERGENTES (REPETITION & TRANSITION AUDITOR)
        all_series_dict = {r: get_history_series(r)[1] for r in RULETAS_CONFIG if RULETAS_CONFIG[r].get("active", False)}
        rep_cache = LIVE_AUDITOR.audit_all_repetition(all_series_dict, RULETAS_CONFIG)
        print("=" * 165)
        print(" 🔁 AGENTE SUPERVISOR DE REPETICIÓN Y PATRONES EMERGENTES (REPETITION & TRANSITION AUDITOR):")
        print("=" * 165)
        headers_rep = f" {'RULETA':<19} | {'REPETICIÓN CONTIGUA':<24} | {'Z-SCORE':<8} | {'REPETICIÓN HOY':<18} | {'PATRONES ACTIVOS':<20} | {'NUEVO PATRÓN EMERGENTE DETECTADO':<60}"
        print(headers_rep)
        print("-" * 165)
        for r_name, cfg_r in RULETAS_CONFIG.items():
            if not cfg_r.get("active", False) or r_name not in rep_cache:
                continue
            r_rep = rep_cache[r_name]
            em = cfg_r.get("emoji", "")
            r_label = f"{em} {r_name}"
            rep_b = r_rep.get("rep_badge", "Normal")
            z_c = f"Z={r_rep.get('z_contig', 0.0):+.2f}"
            rep_h = f"{r_rep.get('dups_today', 0)} dups ({r_rep.get('dup_pct_today', 0.0)}%)"
            
            # Conteo de activos vs fatiga
            snips = r_rep.get("monitored_snipers", [])
            act_cnt = sum(1 for s in snips if s["health"] == "ACTIVO")
            tot_cnt = len(snips)
            snip_str = f"🟢 {act_cnt}/{tot_cnt} Activos" if tot_cnt > 0 else "---"
            
            # Nuevos emergentes
            emerg = r_rep.get("new_emerging", [])
            if emerg:
                top_e = emerg[0]
                emerg_str = f"✨ #{top_e['from_num']} {top_e['from_anim']} -> #{top_e['to_num']} {top_e['to_anim']} (Prob {top_e['prob_pct']}%, Z={top_e['z_score']:+0.2f}, EV +{top_e['ev_pct']}%)"
            else:
                emerg_str = "Ningún patrón anómalo no registrado (Z < +2.8)"
                
            print(f" {r_label:<19} | {rep_b:<24} | {z_c:<8} | {rep_h:<18} | {snip_str:<20} | {emerg_str:<60}")
        print("=" * 165 + "\n")

    return {
        "active_signals": active_signals,
        "radar_items": all_radar_items,
        "bankroll": state["bankroll"]
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bot Cuantitativo Sniper - Nuevas Ruletas")
    parser.add_argument("--check-now", action="store_true", help="Ejecuta un ciclo de monitoreo inmediato")
    parser.add_argument("--status", action="store_true", help="Muestra el estado actual y señales")
    parser.add_argument("--loop", type=int, default=0, help="Ejecuta en bucle continuo cada N segundos")
    args = parser.parse_args()

    if args.loop > 0:
        print(f"🚀 Iniciando Bot Nuevas Ruletas en modo daemon (bucle cada {args.loop}s)...")
        while True:
            try:
                check_and_update(verbose=True)
            except Exception as e:
                print(f"⚠️ Error en ciclo: {e}")
            time.sleep(args.loop)
    else:
        check_and_update(verbose=True)
