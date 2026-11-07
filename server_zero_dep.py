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
import time
import threading
import urllib.request
from http.server import HTTPServer, ThreadingHTTPServer, SimpleHTTPRequestHandler

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
FIXED_STAKE_UNIT = 100.00
DEFAULT_BANKROLL = 20000.0
QUARANTINE_MISSES = 20

RULETAS = {
    "Lotto Gato": {
        "file": os.path.join(ROOT_DIR, "lotto_gato.csv"),
        "title": "Lotto Gato",
        "lags": [18, 38, 14, 25, 30, 35, 40, 45],
        "target_streaks": [1, 2],
        "wr_optimos": [1, 2],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": [],
        "markov_snipers": {"14": "0", "27": "15", "3": "7"},
        "mirror_pairs": {"0": "00", "1": "10", "2": "20", "3": "30", "4": "40"},
        "payout": 60.0,
        "emoji": "🐱"
    },
    "Loto Chaima": {
        "file": os.path.join(ROOT_DIR, "loto_chaima.csv"),
        "title": "Loto Chaima",
        "lags": [49, 41, 35, 56, 61, 66, 71, 76],
        "target_streaks": [0, 1],
        "wr_optimos": [0, 1],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": [],
        "markov_snipers": {"48": "0", "55": "0", "12": "0"},
        "mirror_pairs": {"0": "00", "5": "50", "6": "60", "7": "70"},
        "payout": 60.0,
        "emoji": "🏹"
    },
    "Guacharo Activo": {
        "file": os.path.join(ROOT_DIR, "data_vz", "guacharo_activo_2anios.csv"),
        "title": "Guacharo",
        "lags": [31, 54, 41, 38, 43, 48, 53, 58],
        "target_streaks": [1, 3],
        "wr_optimos": [1, 3, 6],
        "rec_w": 8,
        "anti_clustering": False,
        "blacklist": ["75"],
        "markov_snipers": {"21": "0", "8": "67", "29": "2"},
        "mirror_pairs": {"12": "21", "13": "31", "14": "41", "23": "32"},
        "payout": 60.0,
        "emoji": "🦇"
    },
    "Gatazo": {
        "file": os.path.join(ROOT_DIR, "gatazo.csv"),
        "title": "Gatazo",
        "lags": [35, 9, 20, 42, 47, 52, 57, 62],
        "target_streaks": [1],
        "wr_optimos": [1, 11, 12],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": ["11"],
        "markov_snipers": {"30": "63", "48": "21", "23": "42"},
        "mirror_pairs": {"12": "21", "13": "31", "24": "42", "34": "43"},
        "payout": 60.0,
        "emoji": "🐯"
    },
    "Monje Millonario": {
        "file": os.path.join(ROOT_DIR, "monje_millonario.csv"),
        "title": "Monje Millonario",
        "lags": [24, 42, 48, 31, 36, 41, 46, 51],
        "target_streaks": [0, 1],
        "wr_optimos": [0, 1],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": ["75"],
        "markov_snipers": {},
        "mirror_pairs": {"24": "42"},
        "payout": 60.0,
        "emoji": "🧘‍♂️"
    },
    "Granja Millonaria - Granjazo": {
        "file": os.path.join(ROOT_DIR, "granja_millonaria_granjazo.csv"),
        "title": "Granjazo",
        "lags": [45, 26, 15],
        "target_streaks": [1, 3],
        "wr_optimos": [1, 3],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": [],
        "markov_snipers": {},
        "mirror_pairs": {"15": "51", "26": "62"},
        "payout": 60.0,
        "emoji": "🚜"
    }
}

ANIMALS_MASTER = {
    "0": "DELFÍN", "00": "BALLENA", "1": "CARNERO", "2": "TORO", "3": "CIEMPIÉS",
    "4": "ALACRÁN", "5": "LEÓN", "6": "RANA", "7": "PERICO", "8": "RATÓN",
    "9": "ÁGUILA", "10": "TIGRE", "11": "GATO", "12": "CABALLO", "13": "MONO",
    "14": "PALOMA", "15": "ZORRO", "16": "OSO", "17": "PAVO", "18": "BURRO",
    "19": "CHIVO", "20": "COCHINO", "21": "GALLO", "22": "CAMELLO", "23": "CEBRA",
    "24": "IGUANA", "25": "GALLINA", "26": "VACA", "27": "PERRO", "28": "ZAMURO",
    "29": "ELEFANTE", "30": "CAIMÁN", "31": "LAPA", "32": "ARDILLA", "33": "PESCADO",
    "34": "VENADO", "35": "JIRAFA", "36": "CULEBRA", "37": "TORTUGA", "38": "BÚFALO",
    "39": "LECHUZA", "40": "AVISPA", "41": "CANGURO", "42": "TUCÁN", "43": "MARIPOSA",
    "44": "CHIGÜIRE", "45": "GARZA", "46": "PUMA", "47": "PAVO REAL", "48": "PUERCOESPÍN",
    "49": "PEREZA", "50": "CANARIO", "51": "PELICANO", "52": "PULPO", "53": "CARACOL",
    "54": "GRILLO", "55": "OSO HORMIGUERO", "56": "TIBURÓN", "57": "PATO", "58": "HORMIGA",
    "59": "PANTERA", "60": "CAMALEÓN", "61": "COLIBRÍ", "62": "CACHICAMO", "63": "CANGREJO",
    "64": "GAVILÁN", "65": "ARAÑA", "66": "LOBO", "67": "AVESTRUZ", "68": "JAGUAR",
    "69": "CONEJO", "70": "BISONTE", "71": "GUACAMAYA", "72": "GORILA", "73": "HIPOPÓTAMO",
    "74": "TURPIAL", "75": "CODORNIZ", "76": "MANTIS"
}


def read_csv_series(fpath):
    """Lee un CSV de ruleta devolviendo una lista de diccionarios con fecha, hora, numero y animal."""
    rows = []
    if not os.path.exists(fpath):
        return rows
    try:
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                return rows
            h_map = {col.strip().lower(): idx for idx, col in enumerate(header)}
            f_idx = h_map.get("fecha", 0)
            h_idx = h_map.get("hora", 1)
            n_idx = h_map.get("numero", 2)
            a_idx = h_map.get("animal", 3)
            
            for r in reader:
                if len(r) > max(f_idx, h_idx, n_idx):
                    raw_n = str(r[n_idx]).strip()
                    num = raw_n if raw_n in ("00", "0") else (raw_n.lstrip("0") or "0")
                    anim = str(r[a_idx]).strip() if len(r) > a_idx else ""
                    rows.append({
                        "fecha": str(r[f_idx]).strip(),
                        "hora": str(r[h_idx]).strip(),
                        "numero": num,
                        "animal": anim
                    })
    except Exception as e:
        print(f"Error leyendo {fpath}: {e}")
    return rows


def get_ruleta_filepath(r_name):
    """Localiza el archivo CSV real sin importar cómo se haya descomprimido en el celular."""
    cfg = RULETAS[r_name]
    fname = os.path.basename(cfg["file"])
    candidates = [
        cfg["file"],
        os.path.join(ROOT_DIR, "data_vz", fname),
        os.path.join(ROOT_DIR, fname),
        os.path.join(this_dir, "data_vz", fname),
        os.path.join(this_dir, "sniper", "data_vz", fname),
        os.path.join(this_dir, "..", "data_vz", fname),
        os.path.join(this_dir, fname),
        os.path.join(this_dir, "sniper", fname),
    ]
    for c in candidates:
        if os.path.exists(c) and os.path.getsize(c) > 0:
            return c
    return cfg["file"]


def calcular_peso_agente_pure(r_name, streak, trigger_miss):
    """Agente evaluador por ruleta: devuelve (peso_1_10, label_corto)."""
    cfg = RULETAS.get(r_name, {})
    payout = cfg.get("payout", 30)
    wr_optimos = cfg.get("wr_optimos", [1])

    # Dim 1 - Posicion en racha (0-4 pts)
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

    # Dim 2 - Factor de payout (0-3 pts)
    s_payout = 3 if payout >= 60 else (2 if payout >= 40 else 1)

    # Dim 3 - Rebote post-misses
    if trigger_miss == 0:
        s_miss = 3
    elif trigger_miss <= 2:
        s_miss = 2
    elif trigger_miss <= 5:
        s_miss = 1
    else:
        s_miss = 0

    total = min(10, max(1, s_racha + s_payout + s_miss))
    return total, f"P:{total}/10"


def get_current_streaks(r_name):
    cfg = RULETAS[r_name]
    fpath = get_ruleta_filepath(r_name)
    rows = read_csv_series(fpath)
    if len(rows) < 40:
        return 0, 0, {}

    nums = [r["numero"] for r in rows]
    animals = {r["numero"]: r["animal"] for r in rows}
    dates = [r["fecha"] for r in rows]

    lags = cfg["lags"]
    rec_w = cfg["rec_w"]
    use_anti = cfg["anti_clustering"]
    blacklist = set(cfg["blacklist"])
    target_streaks = cfg.get("target_streaks", [1])

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
        k_cap = cfg.get("k_cap", 0)
        if k_cap and len(cands_lag) > k_cap:
            ord_c = []
            for c in raw_cands:
                if c in cands_lag and c not in ord_c:
                    ord_c.append(c)
                    if len(ord_c) == k_cap:
                        break
            cands_lag = ord_c
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
    k_cap = cfg.get("k_cap", 0)
    if k_cap and len(cands_lag_now) > k_cap:
        ord_c = []
        for c in raw_now:
            if c in cands_lag_now and c not in ord_c:
                ord_c.append(c)
                if len(ord_c) == k_cap:
                    break
        cands_lag_now = ord_c
    
    # Comprobar AntiCluster hoy
    last_date = dates[-1] if dates else ""
    day_nums = [nums[j] for j in range(len(nums)) if dates[j] == last_date]
    is_anti_blocked = bool(use_anti and len(day_nums) >= 2 and day_nums[-1] in day_nums[:-1])

    last_row = rows[-1]
    last_str = f"#{last_row['numero']} {last_row['animal']} ({last_row['hora']})"
    last_num_str = str(last_row["numero"]).strip()

    # Comprobar Markov Sniper & Espejo Sniper
    is_markov = False
    is_mirror = False
    markov_snipers = cfg.get("markov_snipers", {})
    mirror_pairs = cfg.get("mirror_pairs", {})

    if last_num_str in markov_snipers:
        target_num = str(markov_snipers[last_num_str]).strip()
        if target_num not in rec_set_now and target_num not in blacklist:
            is_markov = True
            cands = [target_num]
            anim_name = ANIMALS_MASTER.get(target_num, animals.get(target_num, "OBJETIVO"))
            cands_formatted = [{"numero": target_num, "animal": anim_name}]
        else:
            cands = cands_lag_now if not is_anti_blocked else []
            cands_formatted = [{"numero": c, "animal": ANIMALS_MASTER.get(c, animals.get(c, ""))} for c in cands]
    elif last_num_str in mirror_pairs and not cands_lag_now:
        target_num = str(mirror_pairs[last_num_str]).strip()
        if target_num not in rec_set_now and target_num not in blacklist:
            is_mirror = True
            cands = [target_num]
            anim_name = ANIMALS_MASTER.get(target_num, animals.get(target_num, "ESPEJO"))
            cands_formatted = [{"numero": target_num, "animal": anim_name}]
        else:
            cands = cands_lag_now if not is_anti_blocked else []
            cands_formatted = [{"numero": c, "animal": ANIMALS_MASTER.get(c, animals.get(c, ""))} for c in cands]
    else:
        cands = cands_lag_now if not is_anti_blocked else []
        cands_formatted = [{"numero": c, "animal": ANIMALS_MASTER.get(c, animals.get(c, ""))} for c in cands]

    return streak, trigger_misses, {
        "cands": cands_formatted,
        "is_markov": is_markov,
        "is_mirror": is_mirror,
        "is_anti_blocked": is_anti_blocked,
        "last_str": last_str,
        "last_num": last_row["numero"],
        "last_animal": last_row["animal"],
        "last_hora": last_row["hora"]
    }


def fetch_tuazar_html():
    """Descarga el HTML de TuAzar de forma 100% autonoma y blindada (Cero dependencia de PC)."""
    import subprocess
    import os
    import sys
    import time

    url = "https://www.tuazar.com/loteria/animalitos/resultados/"
    ua = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"

    # Lista de rutas absolutas infalibles para curl_static
    c_paths = [
        os.path.join(this_dir, "curl_static"),
        os.path.join(ROOT_DIR, "curl_static"),
        os.path.join(STATIC_DIR, "curl_static"),
        "/data/data/com.termux/files/usr/bin/curl",
        "/data/data/com.termux/files/home/sniper/curl_static",
        "/data/data/com.termux/files/home/curl_static",
        "./curl_static"
    ]

    valid_curl = None
    for cp in c_paths:
        if os.path.exists(cp) and (os.path.getsize(cp) > 1000000 or "usr/bin/curl" in cp):
            valid_curl = cp
            try:
                os.chmod(cp, 0o777)
            except Exception:
                pass
            break

    # Reintentos con retroceso: 3 intentos para evitar microcortes de datos móviles (4G)
    for intento in range(3):
        # 1. Prioridad: Binario Estático Autónomo
        if valid_curl:
            try:
                res = subprocess.run(
                    [valid_curl, "-k", "-s", "-L", "--connect-timeout", "6", "-m", "10", "-A", ua, url],
                    capture_output=True,
                    timeout=12
                )
                if res.returncode == 0 and len(res.stdout) > 2000:
                    return res.stdout.decode("utf-8", errors="ignore")
            except Exception:
                pass

        # 2. curl en PATH del sistema (Windows o Termux/Linux)
        curl_cmd = "curl.exe" if sys.platform == "win32" else "curl"
        try:
            res = subprocess.run(
                [curl_cmd, "-k", "-s", "-L", "--connect-timeout", "6", "-m", "10", "-A", ua, url],
                capture_output=True,
                timeout=12
            )
            if res.returncode == 0 and len(res.stdout) > 2000:
                return res.stdout.decode("utf-8", errors="ignore")
        except Exception:
            pass

        # 3. urllib estándar si la librería SSL no está dañada
        try:
            import ssl
            import urllib.request
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(url, headers={"User-Agent": ua})
            with urllib.request.urlopen(req, context=ctx, timeout=8) as response:
                html = response.read().decode("utf-8", errors="ignore")
                if len(html) > 2000:
                    return html
        except Exception:
            pass

        time.sleep(1.5)

    return ""

def parse_tuazar_results_pure():
    """Descarga los resultados en vivo de TuAzar y los parsea usando expresiones regulares nativas."""
    extracted = {k: [] for k in RULETAS}
    html = fetch_tuazar_html()
    if not html:
        print("⚠️ No se pudo obtener el HTML de TuAzar.")
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
            if cfg["title"].lower() in title or (r_name == "Granja Millonaria - Granjazo" and "granjazo" in title):
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


def get_ledger_write_path():
    for p in [LEDGER_PATH, os.path.join(this_dir, "ledger_nuevas_ruletas.csv"), os.path.join(ROOT_DIR, "ledger_nuevas_ruletas.csv")]:
        if os.path.exists(p):
            return p
    return LEDGER_PATH


def get_state_write_path():
    for p in [STATE_PATH, os.path.join(this_dir, "state_nuevas_ruletas.json"), os.path.join(ROOT_DIR, "state_nuevas_ruletas.json")]:
        if os.path.exists(p):
            return p
    return STATE_PATH


def load_state_pure():
    spath = get_state_write_path()
    if os.path.exists(spath):
        try:
            with open(spath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "bankroll": 232.0,
        "peak_bankroll": 240.0,
        "total_withdrawn": 734.0,
        "cycle_number": 5,
        "cycle_start_bankroll": 200.0,
        "pending_bets": {}
    }


def save_state_pure(state):
    spath = get_state_write_path()
    try:
        tmp = spath + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        os.replace(tmp, spath)
    except Exception as e:
        print(f"[-] Error guardando estado: {e}")


LEDGER_COLS = [
    "fecha", "hora", "ruleta", "candidatos", "cands_count", "zona_patron",
    "smart_mult", "stake_unit", "total_bet", "resultado", "condicion",
    "cobrado", "pnl", "saldo", "peak", "drawdown_pct"
]


def append_to_ledger_pure(row_dict):
    lpath = get_ledger_write_path()
    file_exists = os.path.exists(lpath) and os.path.getsize(lpath) > 0
    os.makedirs(os.path.dirname(os.path.abspath(lpath)), exist_ok=True)
    with open(lpath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LEDGER_COLS)
        if not file_exists:
            writer.writeheader()
        writer.writerow({c: row_dict.get(c, "") for c in LEDGER_COLS})


def update_csv_files_pure(live_data):
    """Actualiza los CSVs históricos de forma nativa sin pandas."""
    new_counts = {}
    for r_name, items in live_data.items():
        if not items:
            new_counts[r_name] = 0
            continue
        fpath = get_ruleta_filepath(r_name)

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


def evaluate_and_update_all_pure(live_data):
    """
    1. Comprueba nuevos sorteos de TuAzar y los añade a los CSV locales.
    2. Si había una apuesta pendiente en una ruleta con nuevo sorteo:
       - Evalúa si el número salido acertó.
       - Calcula cobrado, PnL y saldo.
       - Registra la fila en ledger_nuevas_ruletas.csv.
       - Elimina la apuesta pendiente.
    3. Reevalúa todas las ruletas para registrar nuevas apuestas pendientes inminentes.
    4. Guarda el estado actualizado.
    """
    new_counts = {}
    new_draws_dict = {}

    for r_name, items in live_data.items():
        if not items:
            new_counts[r_name] = 0
            continue
        fpath = get_ruleta_filepath(r_name)
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
            os.makedirs(os.path.dirname(os.path.abspath(fpath)), exist_ok=True)
            file_exists = os.path.exists(fpath) and os.path.getsize(fpath) > 0
            with open(fpath, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["fecha", "dia", "hora", "numero", "animal", "loteria"])
                for it in new_to_append:
                    writer.writerow([it["fecha"], "", it["hora"], it["numero"], it["animal"], r_name])

        new_counts[r_name] = added
        new_draws_dict[r_name] = new_to_append

    # Cargar estado actual
    state = load_state_pure()
    if "pending_bets" not in state:
        state["pending_bets"] = {}
    bankroll = float(state.get("bankroll", 232.0))
    peak = float(state.get("peak_bankroll", max(240.0, bankroll)))

    # Evaluar sorteos nuevos contra apuestas pendientes
    for r_name, new_items in new_draws_dict.items():
        if not new_items:
            continue
        for it in new_items:
            salido_num = str(it.get("numero", "")).strip()
            salido_anim = str(it.get("animal", "")).strip()
            fecha_res = str(it.get("fecha", "")).strip()
            hora_res = str(it.get("hora", "")).strip()

            if r_name in state["pending_bets"]:
                bet = state["pending_bets"].pop(r_name)
                cands = [str(c) for c in bet.get("candidatos", [])]
                hit = (salido_num in cands)
                stake_unit = float(bet.get("stake_unit", FIXED_STAKE_UNIT))
                payout = float(bet.get("payout", RULETAS.get(r_name, {}).get("payout", 30.0)))
                total_bet = float(bet.get("total_stake", len(cands) * stake_unit))

                cobrado = round(stake_unit * payout, 2) if hit else 0.0
                pnl = round(cobrado - total_bet, 2)
                bankroll = round(bankroll + pnl, 2)
                peak = max(peak, bankroll)
                dd_pct = ((peak - bankroll) / peak * 100.0) if peak > 0 else 0.0

                row_dict = {
                    "fecha": fecha_res,
                    "hora": hora_res,
                    "ruleta": r_name,
                    "candidatos": bet.get("candidatos_str", ", ".join(cands)),
                    "cands_count": bet.get("total_cands", len(cands)),
                    "zona_patron": bet.get("smart_label", "Canasta Rezagados"),
                    "smart_mult": 1.0,
                    "stake_unit": stake_unit,
                    "total_bet": total_bet,
                    "resultado": f"[{salido_num}] {salido_anim}",
                    "condicion": "🟢 GANADA" if hit else "🔴 PERDIDA",
                    "cobrado": cobrado,
                    "pnl": pnl,
                    "saldo": bankroll,
                    "peak": peak,
                    "drawdown_pct": round(dd_pct, 2)
                }
                append_to_ledger_pure(row_dict)
                print(f"[+] 🎯 JUGADA REGISTRADA AUTOMÁTICAMENTE: {r_name} {hora_res} -> {row_dict['condicion']} (PnL: {pnl})")

    # Reevaluar señales inminentes para la siguiente ronda
    color_bubbles = get_30d_color_bubbles(30)
    for r_name, cfg in RULETAS.items():
        stk, miss, info = get_current_streaks(r_name)
        is_markov = info.get("is_markov", False)
        is_anti = info.get("is_anti_blocked", False)
        cands = info.get("cands", [])
        target_streaks = cfg.get("target_streaks", [1])
        burbuja = color_bubbles.get(r_name, {"stake": 1.00})

        is_quar = bool(QUARANTINE_MISSES > 0 and miss >= QUARANTINE_MISSES)
        is_mirror = info.get("is_mirror", False)
        if ((stk in target_streaks or is_markov or is_mirror) and not is_anti and not is_quar):
            if cands and r_name not in state["pending_bets"]:
                cands_nums = [str(c["numero"]) for c in cands]
                p_ag, p_lbl = calcular_peso_agente_pure(r_name, stk, miss)
                cands_str = ", ".join([f"#{c['numero']} {c['animal']} [{p_lbl}]" for c in cands])
                cost = round(len(cands) * FIXED_STAKE_UNIT, 2)
                premio = round(FIXED_STAKE_UNIT * cfg["payout"], 2)
                state["pending_bets"][r_name] = {
                    "ruleta": r_name,
                    "candidatos": cands_nums,
                    "candidatos_str": cands_str,
                    "total_cands": len(cands),
                    "stake_unit": FIXED_STAKE_UNIT,
                    "total_stake": cost,
                    "posible_premio": premio,
                    "payout": cfg["payout"],
                    "peso_agente": p_ag,
                    "peso_label": p_lbl,
                    "smart_label": f"⚡ Markov Sniper [{p_lbl}]" if is_markov else f"🎯 Canasta Rezagados [{p_lbl}]",
                    "last_salido_str": info.get("last_str", "---"),
                    "created_at": datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
                }
                print(f"[*] 🚨 NUEVA SEÑAL REGISTRADA PARA COMPRA: {r_name} -> {cands_str} (${cost} USD)")
        else:
            if r_name in state["pending_bets"]:
                del state["pending_bets"][r_name]

    state["bankroll"] = bankroll
    state["peak_bankroll"] = peak
    save_state_pure(state)
    return new_counts


def read_today_ledger(date_str=None):
    """Lee el registro de operaciones del día desde ledger_nuevas_ruletas.csv sin pandas."""
    if not date_str:
        date_str = datetime.date.today().strftime("%Y-%m-%d")

    candidates = [
        LEDGER_PATH,
        os.path.join(ROOT_DIR, "ledger_nuevas_ruletas.csv"),
        os.path.join(this_dir, "ledger_nuevas_ruletas.csv"),
        os.path.join(this_dir, "sniper", "ledger_nuevas_ruletas.csv"),
        os.path.join(this_dir, "..", "ledger_nuevas_ruletas.csv"),
    ]
    fpath = None
    for c in candidates:
        if os.path.exists(c) and os.path.getsize(c) > 0:
            fpath = c
            break

    if not fpath:
        return [], {
            "ops_today": 0, "wins_today": 0, "inv_today": 0.0, "cob_today": 0.0, "pnl_today": 0.0, "win_rate_today": 0.0
        }

    ops = []
    inv_today = 0.0
    cob_today = 0.0
    wins_today = 0

    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for r in reader:
            fec = str(r.get("fecha", "") or r.get("timestamp", "")).strip().split(" ")[0]
            # Mostrar operaciones de hoy o de ayer (ciclo actual)
            if fec == date_str:
                bet = float(r.get("total_bet", 0.0) or 0.0)
                if bet == 0.0:
                    cands_list = [c for c in str(r.get("candidatos", "")).split(",") if c.strip()]
                    bet = float(len(cands_list) * FIXED_STAKE_UNIT) if cands_list else FIXED_STAKE_UNIT
                cob = float(r.get("cobrado", 0.0) or 0.0)
                pnl = float(r.get("pnl", 0.0) or 0.0)
                saldo = float(r.get("saldo", 0.0) or 0.0)
                r_name = str(r.get("ruleta", "")).strip()

                inv_today += bet
                cob_today += cob
                if pnl > 0 or cob > 0:
                    wins_today += 1

                ops.append({
                    "fecha": fec,
                    "hora": str(r.get("hora", "")).strip(),
                    "ruleta": r_name,
                    "candidatos": str(r.get("candidatos", "")).strip(),
                    "cands_count": int(r.get("cands_count", 1) or 1),
                    "total_bet": bet,
                    "resultado": str(r.get("resultado", "")).strip(),
                    "cobrado": cob,
                    "pnl": pnl,
                    "saldo": saldo,
                    "emoji": RULETAS.get(r_name, {}).get("emoji", "🎲")
                })

    ops_today = len(ops)
    pnl_today = round(cob_today - inv_today, 2)
    win_rate = round((wins_today / ops_today * 100.0) if ops_today > 0 else 0.0, 1)

    stats = {
        "ops_today": ops_today,
        "wins_today": wins_today,
        "inv_today": round(inv_today, 2),
        "cob_today": round(cob_today, 2),
        "pnl_today": pnl_today,
        "win_rate_today": win_rate
    }
    return ops, stats


def sync_from_pc():
    """Modo 100% Autonomo: no bloquea esperando por ninguna PC."""
    pass


def get_30d_color_bubbles(days_window=30):
    """Calcula dinámicamente el rendimiento a 30 días de cada ruleta y asigna burbujas de color y stake."""
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days_window)
    perf = {}
    for r_name, cfg in RULETAS.items():
        fpath = cfg.get("file", "")
        if not os.path.exists(fpath):
            fpath = get_ruleta_filepath(r_name)
        if not os.path.exists(fpath):
            continue
        try:
            records = read_csv_series(fpath)
            lags = cfg["lags"]
            rec_w = cfg["rec_w"]
            anti_clust = cfg.get("anti_clustering", False)
            payout = cfg["payout"]
            streaks = cfg.get("target_streaks", [1])
            
            streak = 0
            cost = 0.0
            rev = 0.0
            seen_today = set()
            last_f = None
            prev_rep = False
            
            min_i = max(lags) + rec_w
            for i in range(min_i, len(records)):
                rec = records[i]
                dt_str = rec.get("fecha", "") + " " + rec.get("hora", "")
                try:
                    dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d %I:%M %p")
                except Exception:
                    continue
                f = rec.get("fecha", "")
                act = rec.get("numero", "")
                if f != last_f:
                    seen_today = set()
                    last_f = f
                    prev_rep = False
                
                recent_window = [r["numero"] for r in records[i-rec_w:i]]
                rec_set = set(recent_window)
                raw = [records[i-l]["numero"] for l in lags if i>=l]
                cands = sorted(list(set(raw) - rec_set))
                cnt = len(cands)
                is_rep = (act in seen_today)
                skip = (anti_clust and prev_rep)
                hit = (act in cands) if cnt > 0 else False
                
                if dt >= cutoff and cnt > 0 and not skip:
                    if streak in streaks:
                        cost += cnt
                        if hit:
                            rev += payout
                    streak = 0 if hit else streak + 1
                elif cnt > 0 and skip:
                    streak = 0 if hit else streak + 1
                seen_today.add(act)
                prev_rep = is_rep
            perf[r_name] = rev - cost
        except Exception:
            perf[r_name] = 0.0
            
    sorted_r = sorted(perf.items(), key=lambda x: x[1], reverse=True)
    tiers = {}
    for rank, (r, pnl_val) in enumerate(sorted_r, 1):
        if rank <= 3:
            tiers[r] = {"rank": rank, "color": "VERDE", "emoji": "🟢", "stake": 1.50, "pnl_30d": round(pnl_val, 2), "color_hex": "#10b981", "badge": "🟢 $1.50"}
        elif rank <= 5:
            tiers[r] = {"rank": rank, "color": "AMARILLO", "emoji": "🟡", "stake": 1.00, "pnl_30d": round(pnl_val, 2), "color_hex": "#f59e0b", "badge": "🟡 $1.00"}
        else:
            tiers[r] = {"rank": rank, "color": "ROJO", "emoji": "🔴", "stake": 0.50, "pnl_30d": round(pnl_val, 2), "color_hex": "#ef4444", "badge": "🔴 $0.50"}
    return tiers


class SniperHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_GET(self):
        if self.path == "/api/status":
            self.handle_api_status()
        elif self.path == "/api/reporte":
            self.handle_api_reporte()
        elif self.path == "/api/tuazar_bridge":
            # Sirve el HTML fresco de TuAzar al celular por HTTP puro
            url = "https://www.tuazar.com/loteria/animalitos/resultados/"
            try:
                import subprocess
                res = subprocess.run([("curl.exe" if sys.platform == "win32" else "curl"), "-k", "-s", "-A", "Mozilla/5.0", url], capture_output=True, timeout=10)
                html_bytes = res.stdout if len(res.stdout) > 2000 else b""
                if not html_bytes:
                    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=10) as r:
                        html_bytes = r.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html_bytes)))
                self.end_headers()
                self.wfile.write(html_bytes)
            except Exception as e:
                self.send_error(500, str(e))
        elif self.path == "/" or self.path.startswith("/index.html") or "?" in self.path:
            html_path = os.path.join(STATIC_DIR, "index.html")
            if not os.path.exists(html_path):
                html_path = os.path.join(ROOT_DIR, "index.html")
            try:
                with open(html_path, "rb") as f:
                    c = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(c)))
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.send_header("Pragma", "no-cache")
                self.send_header("Expires", "0")
                self.end_headers()
                self.wfile.write(c)
            except Exception:
                super().do_GET()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/sync":
            self.handle_api_sync()
        elif self.path == "/api/ingresar_sorteo":
            self.handle_api_ingresar_sorteo()
        elif self.path == "/api/clear_today_ledger":
            self.handle_api_clear_today_ledger()
        else:
            self.send_error(404, "Endpoint no encontrado")

    def handle_api_clear_today_ledger(self):
        """Elimina y archiva el registro de jugadas del día para no saturar la pantalla ni la memoria."""
        try:
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            lpath = get_ledger_write_path()
            removed_count = 0
            if os.path.exists(lpath):
                archive_path = os.path.join(ROOT_DIR, "ledger_archive.csv")
                with open(lpath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                
                if lines:
                    header = lines[0]
                    kept_lines = [header]
                    archived_lines = []
                    for line in lines[1:]:
                        if line.startswith(today_str):
                            archived_lines.append(line)
                            removed_count += 1
                        else:
                            kept_lines.append(line)
                    
                    if archived_lines:
                        file_exists = os.path.exists(archive_path) and os.path.getsize(archive_path) > 0
                        with open(archive_path, "a", encoding="utf-8") as af:
                            if not file_exists:
                                af.write(header)
                            af.writelines(archived_lines)
                    
                    with open(lpath, "w", encoding="utf-8") as f:
                        f.writelines(kept_lines)
            
            state = load_state_pure()
            state["last_ledger_purge"] = datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
            save_state_pure(state)
            
            self.send_json_response({
                "status": "ok", 
                "message": f"Registro diario vaciado con éxito ({removed_count} operaciones archivadas en el historial).",
                "removed_count": removed_count
            })
        except Exception as e:
            self.send_json_response({"status": "error", "message": str(e)}, 500)


    def handle_api_ingresar_sorteo(self):
        """Permite ingresar un resultado manualmente en 0.001s cuando no hay internet."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            req_json = json.loads(post_data.decode('utf-8'))
            
            r_name = req_json.get("ruleta")
            numero = str(req_json.get("numero", "")).strip()
            animal = str(req_json.get("animal", "")).strip()
            hora = req_json.get("hora") or datetime.datetime.now().strftime("%I:%M %p").lstrip("0")
            fecha = req_json.get("fecha") or datetime.date.today().strftime("%Y-%m-%d")
            
            if not r_name or r_name not in RULETAS or not numero:
                self.send_json_response({"status": "error", "message": "Datos incompletos"}, 400)
                return
                
            # Procesar el nuevo sorteo localmente de inmediato
            live_data = {r_name: [{"fecha": fecha, "hora": hora, "numero": numero, "animal": animal}]}
            new_counts = evaluate_and_update_all_pure(live_data)
            
            self.send_json_response({"status": "ok", "message": f"Sorteo registrado: {r_name} {hora} -> #{numero} {animal}", "counts": new_counts})
        except Exception as e:
            self.send_json_response({"status": "error", "message": str(e)}, 500)


    



    def handle_api_status(self):
        try:
            sync_from_pc()
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
            color_bubbles = get_30d_color_bubbles(30)

            # 1. Incluir primero las apuestas pendientes que ya están en el estado
            state = load_state_pure()
            for r_name, pb in state.get("pending_bets", {}).items():
                cfg = RULETAS.get(r_name, {})
                burbuja = color_bubbles.get(r_name, {
                    "color": "AMARILLO", "emoji": "🟡", "stake": 1.00, "rank": 4, 
                    "badge": "🟡 $1.00", "pnl_30d": 0.0, "color_hex": "#f59e0b"
                })
                active_signals.append({
                    "ruleta": r_name,
                    "emoji": cfg.get("emoji", "🎯"),
                    "tipo": pb.get("smart_label", "🚨 Compra Activa"),
                    "candidatos": pb.get("candidatos", []),
                    "candidatos_str": pb.get("candidatos_str", ""),
                    "total_fichas": pb.get("total_cands", 1),
                    "stake_unit": float(pb.get("stake_unit", burbuja["stake"])),
                    "costo": float(pb.get("total_stake", 1.0)),
                    "premio_potencial": float(pb.get("posible_premio", 30.0)),
                    "payout": float(pb.get("payout", 30.0)),
                    "peso_agente": pb.get("peso_agente", 5),
                    "peso_label": pb.get("peso_label", "P:5/10"),
                    "ultimo_salido": pb.get("last_salido_str", "---"),
                    "burbuja": burbuja
                })

            for r_name, cfg in RULETAS.items():
                stk, miss, info = get_current_streaks(r_name)
                is_markov = info.get("is_markov", False)
                is_anti = info.get("is_anti_blocked", False)
                cands = info.get("cands", [])
                target_streaks = cfg.get("target_streaks", [1])

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

                p_agente, p_label = calcular_peso_agente_pure(r_name, stk, miss)
                burbuja = color_bubbles.get(r_name, {
                    "color": "AMARILLO", "emoji": "🟡", "stake": 1.00, "rank": 4, 
                    "badge": "🟡 $1.00", "pnl_30d": 0.0, "color_hex": "#f59e0b"
                })

                # Si no estaba ya en pending_bets, agregar si califica
                is_quar = bool(QUARANTINE_MISSES > 0 and miss >= QUARANTINE_MISSES)
                is_mirror = info.get("is_mirror", False)
                if ((stk in target_streaks or is_markov or is_mirror) and not is_anti and not is_quar) and r_name not in state.get("pending_bets", {}):
                    active_signals.append({
                        "ruleta": r_name,
                        "emoji": cfg["emoji"],
                        "tipo": f"⚡ Markov Sniper [{p_label}]" if is_markov else f"🎯 Canasta Rezagados [{p_label}]",
                        "candidatos": cands,
                        "candidatos_str": ", ".join([f"#{c['numero']} {c['animal']} [{p_label}]" for c in cands]),
                        "total_fichas": len(cands),
                        "stake_unit": burbuja["stake"],
                        "costo": round(len(cands) * burbuja["stake"], 2),
                        "premio_potencial": round(burbuja["stake"] * cfg["payout"], 2),
                        "payout": cfg["payout"],
                        "peso_agente": p_agente,
                        "peso_label": p_label,
                        "ultimo_salido": info.get("last_str", "---"),
                        "burbuja": burbuja
                    })

                c_str = ""
                if urg == 1:
                    if r_name in state.get("pending_bets", {}):
                        c_str = state["pending_bets"][r_name].get("candidatos_str", "")
                    elif cands:
                        c_str = ", ".join([f"#{c['numero']} {c['animal']} [{p_label}]" for c in cands])

                radar_items.append({
                    "ruleta": r_name,
                    "emoji": cfg["emoji"],
                    "payout": cfg["payout"],
                    "racha": stk,
                    "misses": miss,
                    "badge": badge,
                    "conteo_str": conteo,
                    "urgencia": urg,
                    "peso_agente": p_agente,
                    "peso_label": p_label,
                    "ultimo_salido": info.get("last_str", "---"),
                    "is_markov": False,
                    "is_anti_blocked": is_anti,
                    "burbuja": burbuja,
                    "candidatos_str": c_str
                })

            radar_items.sort(key=lambda x: (x["urgencia"], x["racha"]))

            recent_ledger, stats_today = read_today_ledger()

            resp = {
                "status": "ok",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
                "hora": datetime.datetime.now().strftime("%I:%M %p").lstrip("0"),
                "wallet": {
                    "bankroll": bankroll,
                    "withdrawn": withdrawn,
                    "patrimonio": patrimonio,
                    "cycle_num": state.get("cycle_number", 5),
                    "cycle_base": cycle_base,
                    "cycle_pnl": cycle_pnl,
                    "cycle_pct": cycle_pct,
                    "pnl_today": stats_today["pnl_today"],
                    "ops_today": stats_today["ops_today"],
                    "wins_today": stats_today["wins_today"],
                    "inv_today": stats_today["inv_today"],
                    "cob_today": stats_today["cob_today"],
                    "win_rate_today": stats_today["win_rate_today"]
                },
                "active_signals": active_signals,
                "radar_items": radar_items,
                "recent_ledger": recent_ledger
            }
            self.send_json_response(resp)
        except Exception as e:
            self.send_json_response({"status": "error", "message": str(e)}, 500)

    def handle_api_sync(self):
        try:
            sync_from_pc()
            live_data = parse_tuazar_results_pure()
            new_counts = evaluate_and_update_all_pure(live_data)
            self.send_json_response({
                "status": "ok",
                "total_new_draws": sum(new_counts.values()),
                "new_counts": new_counts,
                "synced_at": datetime.datetime.now().strftime("%I:%M:%S %p")
            })
        except Exception as e:
            self.send_json_response({"status": "error", "message": str(e)}, 500)

    def handle_api_reporte(self):
        try:
            candidates = [
                os.path.join(ROOT_DIR, "reporte_horario.py"),
                os.path.join(this_dir, "reporte_horario.py"),
                os.path.join(this_dir, "sniper", "reporte_horario.py"),
                os.path.join(this_dir, "..", "reporte_horario.py"),
            ]
            fpath = None
            for c in candidates:
                if os.path.exists(c):
                    fpath = c
                    break

            txt = ""
            if fpath:
                import importlib.util
                spec = importlib.util.spec_from_file_location("reporte_horario", fpath)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                txt = mod.generate_hourly_report()
            else:
                txt = "## ⏱️ Reporte Táctico\n\nNo se localizó el generador reporte_horario.py."
            self.send_json_response({"status": "ok", "reporte": txt})
        except Exception as e:
            self.send_json_response({"status": "error", "message": str(e)}, 500)

    def send_json_response(self, data, code=200):
        try:
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            print(f"[-] Error enviando JSON: {e}")


def start_background_auto_sync():
    """Hilo daemon que sincroniza con la PC (si está encendida) y con TuAzar automáticamente cada 60 segundos."""
    def _worker():
        time.sleep(3)
        while True:
            try:
                sync_from_pc()
                live_data = parse_tuazar_results_pure()
                if live_data:
                    new_counts = evaluate_and_update_all_pure(live_data)
                    tot = sum(new_counts.values())
                    if tot > 0:
                        print(f"[{datetime.datetime.now().strftime('%I:%M:%S %p')}] 🔄 Sincronización automática: {tot} sorteos procesados.")
            except Exception as e:
                pass
            time.sleep(60)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    print("[*] 🤖 Auto-Pilot activado: verificando sorteos y registrando jugadas cada 60 segundos.")


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    port = int(os.environ.get("PORT", 5000))
    print("=" * 80)
    print(f"[*] SERVIDOR STANDALONE CERO-DEPENDENCIAS INICIADO EN PUERTO {port}")
    print(f"   • Abre en tu celular: http://localhost:{port}")
    print("   • No requiere 'pip install', corre con el Python nativo de Termux.")
    print("=" * 80)
    # Activar wake-lock de Termux automaticamente para que no se duerma con la pantalla apagada
    try:
        import subprocess
        subprocess.run(["termux-wake-lock"], capture_output=True, timeout=2)
        print("[*] 🔒 Termux Wake-Lock activado (operación continua en segundo plano).")
    except Exception:
        pass
    # Sincronización bajo demanda (Ahorro de batería y sin saturar red)
    print("[*] 🛡️ Modo Bajo Demanda Activado: Las actualizaciones se realizan al tocar 'TuAzar' en la app.")
    server = ThreadingHTTPServer(("0.0.0.0", port), SniperHandler)
    server.serve_forever()
