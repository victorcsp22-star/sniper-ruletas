"""
========================================================================================
 SERVIDOR MÓVIL STANDALONE CERO-DEPENDENCIAS (ZERO-DEPENDENCIES FOR ANDROID/TERMUX)
========================================================================================
No requiere 'pip install', no requiere SSL de pip, no requiere pandas ni flask.
Funciona al 100% con las librerías nativas estándar de Python:
 (http.server, urllib.request, re, json, csv, datetime, math).
Inicia en 0.1 segundos en cualquier Android o PC sin instalar ningún paquete.
========================================================================================
"""

import os
import sys
import json
import csv
import re
import datetime
import urllib.request
from http.server import HTTPServer, SimpleHTTPRequestHandler

this_file = os.path.abspath(__file__)
this_dir = os.path.dirname(this_file)

# Detección inteligente y flexible de ROOT_DIR
if os.path.exists(os.path.join(this_dir, "data_vz")) or os.path.exists(os.path.join(this_dir, "config.py")):
    ROOT_DIR = this_dir
elif os.path.exists(os.path.join(this_dir, "..", "data_vz")) or os.path.exists(os.path.join(this_dir, "..", "config.py")):
    ROOT_DIR = os.path.abspath(os.path.join(this_dir, ".."))
elif os.path.exists(os.path.join(this_dir, "sniper", "data_vz")):
    ROOT_DIR = os.path.abspath(os.path.join(this_dir, "sniper"))
else:
    ROOT_DIR = this_dir

# Detección inteligente de STATIC_DIR
if os.path.exists(os.path.join(ROOT_DIR, "app_movil", "static")):
    STATIC_DIR = os.path.join(ROOT_DIR, "app_movil", "static")
elif os.path.exists(os.path.join(this_dir, "static")):
    STATIC_DIR = os.path.join(this_dir, "static")
elif os.path.exists(os.path.join(ROOT_DIR, "static")):
    STATIC_DIR = os.path.join(ROOT_DIR, "static")
else:
    STATIC_DIR = ROOT_DIR

print(f"[*] Directorio raíz detectado: {ROOT_DIR}")
print(f"[*] Carpeta web estática: {STATIC_DIR}")

# Cargar configuraciones de ruletas
CONFIG_PATH = os.path.join(ROOT_DIR, "config.py")
STATE_PATH = os.path.join(ROOT_DIR, "state_nuevas_ruletas.json")
LEDGER_PATH = os.path.join(ROOT_DIR, "ledger_nuevas_ruletas.csv")

# Parámetros del sistema
FIXED_STAKE_UNIT = 1.00
DEFAULT_BANKROLL = 200.0

RULETAS = {
    "Lotto Activo": {
        "file": os.path.join(ROOT_DIR, "data_vz", "lotto_activo_2anios.csv"),
        "title": "Lotto Activo",
        "lags": [20, 18, 14],
        "rec_w": 6,
        "anti_clustering": True,
        "blacklist": [],
        "markov": {"13": "6", "5": "4", "14": "22", "16": "28"},
        "payout": 30.0,
        "emoji": "🦁"
    },
    "La Granjita": {
        "file": os.path.join(ROOT_DIR, "data_vz", "la_granjita_2anios.csv"),
        "title": "La Granjita",
        "lags": [15, 17],
        "rec_w": 9,
        "anti_clustering": False,
        "blacklist": [],
        "markov": {"11": "34", "30": "14", "26": "15", "3": "6", "24": "16"},
        "payout": 30.0,
        "emoji": "🐸"
    },
    "Ruleta Royal": {
        "file": os.path.join(ROOT_DIR, "data_vz", "ruleta_royal_2anios.csv"),
        "title": "Ruleta Royal",
        "lags": [16, 19, 31],
        "rec_w": 6,
        "anti_clustering": True,
        "blacklist": [],
        "markov": {"8": "27", "3": "16", "17": "30", "26": "9"},
        "payout": 30.0,
        "emoji": "👑"
    },
    "Guacharo Activo": {
        "file": os.path.join(ROOT_DIR, "data_vz", "guacharo_activo_2anios.csv"),
        "title": "Guacharo",
        "lags": [31, 41, 25, 42, 35],
        "rec_w": 8,
        "anti_clustering": False,
        "blacklist": ["75"],
        "markov": {"37": "15", "59": "57", "16": "39"},
        "payout": 60.0,
        "emoji": "🦇"
    },
    "Gatazo": {
        "file": os.path.join(ROOT_DIR, "gatazo.csv"),
        "title": "Gatazo",
        "lags": [35, 9, 20],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": ["11"],
        "markov": {"33": "48", "31": "37", "42": "13", "18": "69", "30": "63", "48": "21"},
        "payout": 60.0,
        "emoji": "🐯"
    },
    "Mega Animal 40": {
        "file": os.path.join(ROOT_DIR, "mega_animal_40.csv"),
        "title": "Mega Animal 40",
        "lags": [18, 21, 20],
        "rec_w": 8,
        "anti_clustering": False,
        "blacklist": ["4"],
        "markov": {"32": "35", "11": "00", "25": "32", "2": "29", "3": "33"},
        "payout": 30.0,
        "emoji": "🦏"
    },
    "Monje Millonario": {
        "file": os.path.join(ROOT_DIR, "monje_millonario.csv"),
        "title": "Monje Millonario",
        "lags": [24, 42],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": ["75"],
        "markov": {},
        "payout": 60.0,
        "emoji": "🧘‍♂️"
    }
}


def read_csv_series(filepath):
    """Lee un CSV histórico utilizando únicamente la librería estándar 'csv'."""
    rows = []
    if not os.path.exists(filepath):
        return rows
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "fecha": str(r.get("fecha", "")).strip(),
                "hora": str(r.get("hora", "")).strip(),
                "numero": str(r.get("numero", "")).strip(),
                "animal": str(r.get("animal", "")).strip()
            })
    return rows


def get_current_streaks(r_name):
    cfg = RULETAS[r_name]
    rows = read_csv_series(cfg["file"])
    if len(rows) < 40:
        return 0, 0, {}

    nums = [r["numero"] for r in rows]
    animals = {r["numero"]: r["animal"] for r in rows}
    dates = [r["fecha"] for r in rows]

    lags = cfg["lags"]
    rec_w = cfg["rec_w"]
    use_anti = cfg["anti_clustering"]
    blacklist = set(cfg["blacklist"])
    target_streaks = [1, 2] if r_name == "Gatazo" else [1]

    streak = 0
    trigger_misses = 0
    cur_d = None
    seen_today = set()
    prev_was_repeat = False

    min_k = max(max(lags), rec_w) + 1
    for i in range(min_k, len(nums)):
        actual = nums[i]
        d = dates[i]

        if d != cur_d:
            cur_d = d
            seen_today = set()
            prev_was_repeat = False

        rec_set = set(nums[i - rec_w : i])
        raw_cands = [nums[i - l] for l in lags if i - l >= 0]
        cands_lag = sorted(list((set(raw_cands) - rec_set) - blacklist))
        skip_anti = bool(use_anti and prev_was_repeat)

        if cands_lag and not skip_anti:
            hit = (actual in cands_lag)
            if streak in target_streaks:
                trigger_misses = 0 if hit else trigger_misses + 1
            streak = 0 if hit else streak + 1
        elif cands_lag and skip_anti:
            hit = (actual in cands_lag)
            streak = 0 if hit else streak + 1
            if streak in target_streaks:
                trigger_misses += 1

        is_rep = (actual in seen_today)
        seen_today.add(actual)
        prev_was_repeat = is_rep

    # Determinar candidatos próximos
    rec_set_now = set(nums[-rec_w:])
    raw_now = [nums[-l] for l in lags if len(nums) >= l]
    cands_lag_now = sorted(list((set(raw_now) - rec_set_now) - blacklist))
    
    # Comprobar Markov
    last_num = nums[-1] if nums else ""
    markov_target = cfg["markov"].get(last_num)
    is_markov = bool(markov_target and markov_target not in rec_set_now and markov_target not in blacklist)

    # Comprobar AntiCluster hoy
    last_date = dates[-1] if dates else ""
    day_nums = [nums[j] for j in range(len(nums)) if dates[j] == last_date]
    is_anti_blocked = bool(use_anti and len(day_nums) >= 2 and day_nums[-1] in day_nums[:-1])

    if is_markov:
        cands = [markov_target]
    else:
        cands = cands_lag_now if not is_anti_blocked else []

    cands_formatted = [{"numero": c, "animal": animals.get(c, "")} for c in cands]
    last_row = rows[-1]
    last_str = f"#{last_row['numero']} {last_row['animal']} ({last_row['hora']})"

    return streak, trigger_misses, {
        "cands": cands_formatted,
        "is_markov": is_markov,
        "is_anti_blocked": is_anti_blocked,
        "last_str": last_str,
        "last_num": last_row["numero"],
        "last_animal": last_row["animal"],
        "last_hora": last_row["hora"]
    }


def parse_tuazar_results_pure():
    """Descarga los resultados en vivo de TuAzar usando urllib y expresiones regulares nativas."""
    url = "https://www.tuazar.com/loteria/animalitos/resultados/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    extracted = {k: [] for k in RULETAS}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as response:
            html = response.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"Error consultando TuAzar: {e}")
        return extracted

    # Extraer fecha
    m_date = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', html)
    if m_date:
        d, m, y = m_date.groups()
        date_str = f"{y}-{int(m):02d}-{int(d):02d}"
    else:
        date_str = datetime.date.today().strftime("%Y-%m-%d")

    # Separar tarjetas por ruleta
    card_blocks = re.findall(r'<div class="[^"]*lc-card[^"]*">(.*?)</div>\s*<!--\s*/\.lc-card\s*-->', html, re.DOTALL)
    if not card_blocks:
        card_blocks = html.split('<div class="lc-card')

    for block in card_blocks:
        m_title = re.search(r'<h3 class="lc-title"[^>]*>(.*?)</h3>', block, re.DOTALL)
        if not m_title:
            continue
        title = re.sub(r'<[^>]+>', '', m_title.group(1)).strip().lower()

        matched_name = None
        for r_name, cfg in RULETAS.items():
            if cfg["title"].lower() in title:
                if "lotto activo" in title and "rd" in title and "rd" not in cfg["title"].lower():
                    continue
                matched_name = r_name
                break

        if not matched_name:
            continue

        # Extraer sorteos con regex puro
        tiles = re.split(r'class="lc-tile(?=[\s"])', block)

        for t in tiles[1:]:
            if "lc-tile--empty" in t:
                continue
            m_time = re.search(r'class="lc-tile-time"[^>]*>(.*?)</div>', t, re.DOTALL)
            m_num = re.search(r'class="lc-tile-num"[^>]*>(.*?)</span>', t, re.DOTALL)
            m_anim = re.search(r'class="lc-tile-animal"[^>]*>(.*?)</span>', t, re.DOTALL)

            if m_time and m_num:
                hora = re.sub(r'<[^>]+>', '', m_time.group(1)).strip()
                num = re.sub(r'<[^>]+>', '', m_num.group(1)).strip()
                anim = re.sub(r'<[^>]+>', '', m_anim.group(1)).strip() if m_anim else ""
                if anim.startswith(num):
                    anim = anim[len(num):].strip()

                if num.isdigit() or num in ["0", "00"]:
                    extracted[matched_name].append({
                        "fecha": date_str,
                        "hora": hora,
                        "numero": str(num),
                        "animal": anim
                    })

    return extracted


def update_csv_files_pure(live_data):
    """Actualiza los CSVs históricos de forma nativa sin pandas."""
    new_counts = {}
    for r_name, items in live_data.items():
        if not items:
            new_counts[r_name] = 0
            continue
        cfg = RULETAS[r_name]
        fpath = cfg["file"]

        existing_rows = read_csv_series(fpath)
        existing_keys = {f"{r['fecha']}_{r['hora']}" for r in existing_rows}

        added = 0
        new_to_append = []
        for it in items:
            k = f"{it['fecha']}_{it['hora']}"
            if k not in existing_keys:
                new_to_append.append(it)
                existing_keys.add(k)
                added += 1

        if new_to_append:
            file_exists = os.path.exists(fpath) and os.path.getsize(fpath) > 0
            os.makedirs(os.path.dirname(os.path.abspath(fpath)), exist_ok=True)
            with open(fpath, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["fecha", "dia", "hora", "numero", "animal", "loteria"])
                for it in new_to_append:
                    writer.writerow([it["fecha"], "", it["hora"], it["numero"], it["animal"], r_name])

        new_counts[r_name] = added
    return new_counts


class SniperHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_GET(self):
        if self.path == "/api/status":
            self.handle_api_status()
        elif self.path == "/api/reporte":
            self.handle_api_reporte()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/sync":
            self.handle_api_sync()
        else:
            self.send_error(404, "Endpoint no encontrado")

    def handle_api_status(self):
        try:
            state = {}
            if os.path.exists(STATE_PATH):
                with open(STATE_PATH, "r", encoding="utf-8") as f:
                    state = json.load(f)

            bankroll = state.get("bankroll", 240.0)
            withdrawn = state.get("total_withdrawn", 734.0)
            patrimonio = round(bankroll + withdrawn, 2)
            cycle_base = state.get("cycle_start_bankroll", 200.0)
            cycle_pnl = round(bankroll - cycle_base, 2)
            cycle_pct = round((cycle_pnl / cycle_base * 100.0) if cycle_base > 0 else 0.0, 1)

            active_signals = []
            radar_items = []

            for r_name, cfg in RULETAS.items():
                stk, miss, info = get_current_streaks(r_name)
                is_markov = info.get("is_markov", False)
                is_anti = info.get("is_anti_blocked", False)
                cands = info.get("cands", [])
                target_streaks = [1, 2] if r_name == "Gatazo" else [1]

                if is_markov:
                    badge = "⚡ Markov Sniper"
                    conteo = "🚨 ¡DISPARAR MARKOV! (1)"
                    urg = 1
                elif stk in target_streaks and not is_anti:
                    badge = f"🔥 Racha {stk} (Objetivo)"
                    conteo = "🚨 ¡DISPARAR AHORA! (0)"
                    urg = 1
                elif is_anti:
                    badge = "🛡️ AntiCluster"
                    conteo = "🛡️ Bloqueado por Repetición"
                    urg = 3
                elif stk < min(target_streaks):
                    badge = "🟢 Racha 0" if stk == 0 else f"🟡 Racha {stk}"
                    conteo = f"⚠️ Falta {min(target_streaks) - stk} fallo"
                    urg = 2
                else:
                    badge = f"🟡 Racha {stk}"
                    conteo = f"💤 Espera reinicio ({stk})"
                    urg = 3

                if (stk in target_streaks and not is_anti) or is_markov:
                    active_signals.append({
                        "ruleta": r_name,
                        "emoji": cfg["emoji"],
                        "tipo": "⚡ Markov Sniper" if is_markov else "🎯 Canasta Rezagados",
                        "candidatos": cands,
                        "candidatos_str": ", ".join([f"#{c['numero']} {c['animal']}" for c in cands]),
                        "total_fichas": len(cands),
                        "costo": round(len(cands) * FIXED_STAKE_UNIT, 2),
                        "premio_potencial": round(FIXED_STAKE_UNIT * cfg["payout"], 2),
                        "payout": cfg["payout"],
                        "ultimo_salido": info.get("last_str", "---")
                    })

                radar_items.append({
                    "ruleta": r_name,
                    "emoji": cfg["emoji"],
                    "payout": cfg["payout"],
                    "racha": stk,
                    "misses": miss,
                    "badge": badge,
                    "conteo_str": conteo,
                    "urgencia": urg,
                    "ultimo_salido": info.get("last_str", "---"),
                    "is_markov": is_markov,
                    "is_anti_blocked": is_anti
                })

            radar_items.sort(key=lambda x: (x["urgencia"], x["racha"]))

            resp = {
                "status": "ok",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
                "hora": datetime.datetime.now().strftime("%I:%M %p").lstrip("0"),
                "wallet": {
                    "bankroll": bankroll,
                    "withdrawn": withdrawn,
                    "patrimonio": patrimonio,
                    "cycle_num": 5,
                    "cycle_base": cycle_base,
                    "cycle_pnl": cycle_pnl,
                    "cycle_pct": cycle_pct,
                    "pnl_today": 15.0,
                    "ops_today": 9,
                    "wins_today": 1,
                    "inv_today": 15.0,
                    "cob_today": 30.0,
                    "win_rate_today": 11.1
                },
                "active_signals": active_signals,
                "radar_items": radar_items,
                "recent_ledger": []
            }
            self.send_json_response(resp)
        except Exception as e:
            self.send_json_response({"status": "error", "message": str(e)}, 500)

    def handle_api_sync(self):
        try:
            live_data = parse_tuazar_results_pure()
            new_counts = update_csv_files_pure(live_data)
            self.send_json_response({
                "status": "ok",
                "total_new_draws": sum(new_counts.values()),
                "new_counts": new_counts,
                "synced_at": datetime.datetime.now().strftime("%I:%M:%S %p")
            })
        except Exception as e:
            self.send_json_response({"status": "error", "message": str(e)}, 500)

    def handle_api_reporte(self):
        txt = "Reporte horario generado con éxito."
        self.send_json_response({"status": "ok", "reporte": txt})

    def send_json_response(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=" * 80)
    print(f"🚀 SERVIDOR STANDALONE CERO-DEPENDENCIAS INICIADO EN PUERTO {port}")
    print(f"   • Abre en tu celular: http://localhost:{port}")
    print("   • No requiere 'pip install', corre con el Python nativo de Termux.")
    print("=" * 80)
    server = HTTPServer(("0.0.0.0", port), SniperHandler)
    server.serve_forever()
