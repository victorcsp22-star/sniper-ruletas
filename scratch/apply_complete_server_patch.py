import os
import sys

base_dir = r"C:\Users\victo\nuevas_ruletas"
server_file = os.path.join(base_dir, "app_movil", "server_zero_dep.py")

with open(server_file, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update RULETAS dictionary to include markov_snipers and mirror_pairs
target_ruletas = '''RULETAS = {
    "Mega Animal 40": {
        "file": os.path.join(ROOT_DIR, "mega_animal_40.csv"),
        "title": "Mega Animal 40",
        "lags": [18, 21, 22, 20, 43, 46],
        "target_streaks": [1, 2, 3],
        "wr_optimos": [1, 2, 3],
        "rec_w": 8,
        "anti_clustering": False,
        "blacklist": ["4"],
        "payout": 30.0,
        "emoji": "🦏"
    },
    "Gatazo": {
        "file": os.path.join(ROOT_DIR, "gatazo.csv"),
        "title": "Gatazo",
        "lags": [35, 22, 20, 9],
        "target_streaks": [1, 2],
        "wr_optimos": [1, 2],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": ["11"],
        "payout": 60.0,
        "emoji": "🐯"
    },
    "Monje Millonario": {
        "file": os.path.join(ROOT_DIR, "monje_millonario.csv"),
        "title": "Monje Millonario",
        "lags": [24, 42, 52, 51, 48, 35, 23, 44],
        "target_streaks": [0, 1],
        "wr_optimos": [0, 1],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": ["75"],
        "payout": 60.0,
        "emoji": "🧘"
    },
    "Lotto Activo": {
        "file": os.path.join(ROOT_DIR, "data_vz", "lotto_activo_2anios.csv"),
        "title": "Lotto Activo",
        "lags": [20, 18, 19, 14, 15, 55],
        "target_streaks": [1, 2],
        "wr_optimos": [1, 2],
        "rec_w": 6,
        "anti_clustering": True,
        "blacklist": [],
        "payout": 30.0,
        "emoji": "🦁"
    },
    "Ruleta Royal": {
        "file": os.path.join(ROOT_DIR, "data_vz", "ruleta_royal_2anios.csv"),
        "title": "Ruleta Royal",
        "lags": [16, 19, 31],
        "target_streaks": [1],
        "wr_optimos": [1],
        "rec_w": 6,
        "anti_clustering": True,
        "blacklist": [],
        "payout": 30.0,
        "emoji": "👑"
    },
    "Guacharo Activo": {
        "file": os.path.join(ROOT_DIR, "data_vz", "guacharo_activo_2anios.csv"),
        "title": "Guacharo",
        "lags": [41, 54, 31, 52, 42, 25, 35, 21],
        "target_streaks": [1, 3],
        "wr_optimos": [1, 3],
        "rec_w": 8,
        "anti_clustering": False,
        "blacklist": ["75"],
        "payout": 60.0,
        "emoji": "🦇"
    },
    "Lotto Gato": {
        "file": os.path.join(ROOT_DIR, "lotto_gato.csv"),
        "title": "Lotto Gato",
        "lags": [18, 38, 16],
        "target_streaks": [1, 2],
        "wr_optimos": [1, 2],
        "rec_w": 8,
        "anti_clustering": True,
        "blacklist": [],
        "payout": 30.0,
        "emoji": "🐱"
    },
    "Granja Millonaria - Granjazo": {
        "file": os.path.join(ROOT_DIR, "granja_millonaria_granjazo.csv"),
        "title": "Granjazo",
        "lags": [15, 48, 45, 26],
        "target_streaks": [1],
        "wr_optimos": [1],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": [],
        "payout": 60.0,
        "emoji": "🚜"
    }
}'''

replacement_ruletas = '''RULETAS = {
    "Mega Animal 40": {
        "file": os.path.join(ROOT_DIR, "mega_animal_40.csv"),
        "title": "Mega Animal 40",
        "lags": [18, 21, 22, 20, 43, 46],
        "target_streaks": [1, 2, 3],
        "wr_optimos": [1, 2, 3],
        "rec_w": 8,
        "anti_clustering": False,
        "blacklist": ["4"],
        "markov_snipers": {"30": "0", "11": "0", "32": "35"},
        "mirror_pairs": {"11": "00", "12": "21", "13": "31", "23": "32"},
        "payout": 30.0,
        "emoji": "🦏"
    },
    "Gatazo": {
        "file": os.path.join(ROOT_DIR, "gatazo.csv"),
        "title": "Gatazo",
        "lags": [35, 22, 20, 9],
        "target_streaks": [1, 2],
        "wr_optimos": [1, 2],
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
        "lags": [24, 42, 52, 51, 48, 35, 23, 44],
        "target_streaks": [0, 1],
        "wr_optimos": [0, 1],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": ["75"],
        "markov_snipers": {},
        "mirror_pairs": {"24": "42"},
        "payout": 60.0,
        "emoji": "🧘"
    },
    "Lotto Activo": {
        "file": os.path.join(ROOT_DIR, "data_vz", "lotto_activo_2anios.csv"),
        "title": "Lotto Activo",
        "lags": [20, 18, 19, 14, 15, 55],
        "target_streaks": [1, 2],
        "wr_optimos": [1, 2],
        "rec_w": 6,
        "anti_clustering": True,
        "blacklist": [],
        "markov_snipers": {"14": "0", "31": "0", "6": "0"},
        "mirror_pairs": {"12": "21", "13": "31", "23": "32", "0": "00"},
        "payout": 30.0,
        "emoji": "🦁"
    },
    "Ruleta Royal": {
        "file": os.path.join(ROOT_DIR, "data_vz", "ruleta_royal_2anios.csv"),
        "title": "Ruleta Royal",
        "lags": [16, 19, 31],
        "target_streaks": [1],
        "wr_optimos": [1],
        "rec_w": 6,
        "anti_clustering": True,
        "blacklist": [],
        "markov_snipers": {"25": "22", "8": "27"},
        "mirror_pairs": {"12": "21", "13": "31", "23": "32"},
        "payout": 30.0,
        "emoji": "👑"
    },
    "Guacharo Activo": {
        "file": os.path.join(ROOT_DIR, "data_vz", "guacharo_activo_2anios.csv"),
        "title": "Guacharo",
        "lags": [41, 54, 31, 52, 42, 25, 35, 21],
        "target_streaks": [1, 3],
        "wr_optimos": [1, 3],
        "rec_w": 8,
        "anti_clustering": False,
        "blacklist": ["75"],
        "markov_snipers": {"21": "0", "8": "67", "29": "2"},
        "mirror_pairs": {"12": "21", "13": "31", "14": "41", "23": "32"},
        "payout": 60.0,
        "emoji": "🦇"
    },
    "Lotto Gato": {
        "file": os.path.join(ROOT_DIR, "lotto_gato.csv"),
        "title": "Lotto Gato",
        "lags": [18, 38, 16],
        "target_streaks": [1, 2],
        "wr_optimos": [1, 2],
        "rec_w": 8,
        "anti_clustering": True,
        "blacklist": [],
        "markov_snipers": {"14": "0", "27": "15", "3": "7"},
        "mirror_pairs": {"0": "00", "1": "10", "2": "20", "3": "30", "4": "40"},
        "payout": 30.0,
        "emoji": "🐱"
    },
    "Granja Millonaria - Granjazo": {
        "file": os.path.join(ROOT_DIR, "granja_millonaria_granjazo.csv"),
        "title": "Granjazo",
        "lags": [15, 48, 45, 26],
        "target_streaks": [1],
        "wr_optimos": [1],
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
}'''

assert target_ruletas in code, "No se encontró target_ruletas"
code = code.replace(target_ruletas, replacement_ruletas)

# 2. Fix read_csv_series lstrip("0") bug
target_csv = 'num = str(r[n_idx]).strip().lstrip("0") or "0"'
replacement_csv = '''raw_n = str(r[n_idx]).strip()
                    num = raw_n if raw_n in ("00", "0") else (raw_n.lstrip("0") or "0")'''
assert target_csv in code, "No se encontró target_csv"
code = code.replace(target_csv, replacement_csv)

# 3. Fix get_current_streaks to support Markov & Mirror & Master Animals
target_streaks_eval = '''    # Comprobar Markov Sniper
    is_markov = False
    markov_snipers = cfg.get("markov_snipers", {})
    if last_num_str in markov_snipers:
        target_num = markov_snipers[last_num_str]
        if target_num not in rec_set_now and target_num not in blacklist:
            is_markov = True
            cands = [target_num]
            cands_formatted = [{"numero": target_num, "animal": animals.get(target_num, "")}]
        else:
            cands = cands_lag_now if not is_anti_blocked else []
            cands_formatted = [{"numero": c, "animal": animals.get(c, "")} for c in cands]
    else:
        cands = cands_lag_now if not is_anti_blocked else []
        cands_formatted = [{"numero": c, "animal": animals.get(c, "")} for c in cands]

    return streak, trigger_misses, {
        "cands": cands_formatted,
        "is_markov": is_markov,
        "is_anti_blocked": is_anti_blocked,
        "last_str": last_str,
        "last_num": last_row["numero"],
        "last_animal": last_row["animal"],
        "last_hora": last_row["hora"]
    }'''

replacement_streaks_eval = '''    # Comprobar Markov Sniper & Espejo Sniper
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
    }'''

assert target_streaks_eval in code, "No se encontró target_streaks_eval"
code = code.replace(target_streaks_eval, replacement_streaks_eval)

with open(server_file, "w", encoding="utf-8") as f:
    f.write(code)

print("¡server_zero_dep.py actualizado exitosamente!")
