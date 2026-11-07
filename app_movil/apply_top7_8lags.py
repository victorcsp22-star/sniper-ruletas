import sys
import re

server_path = r'C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py'

with open(server_path, 'r', encoding='utf-8') as f:
    code = f.read()

# Definicion exacta de las 7 Ruletas Maestras con 8 Lags
new_ruletas_block = """RULETAS = {
    "Lotto Gato": {
        "file": os.path.join(ROOT_DIR, "lotto_gato.csv"),
        "title": "Lotto Gato",
        "lags": [18, 38, 14, 25, 30, 35, 40, 45],
        "target_streaks": [1, 2],
        "wr_optimos": [1, 2],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": [],
        "markov": {},
        "mirror": {},
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
        "markov": {},
        "mirror": {},
        "payout": 60.0,
        "emoji": "🦜"
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
        "markov": {},
        "mirror": {},
        "payout": 60.0,
        "emoji": "🦇"
    },
    "Ruleta Royal": {
        "file": os.path.join(ROOT_DIR, "data_vz", "ruleta_royal_2anios.csv"),
        "title": "Ruleta Royal",
        "lags": [19, 16, 31, 26, 31, 36, 41, 46],
        "target_streaks": [1],
        "wr_optimos": [0, 1, 6],
        "rec_w": 6,
        "anti_clustering": True,
        "blacklist": [],
        "markov": {},
        "mirror": {},
        "payout": 30.0,
        "emoji": "👑"
    },
    "Gatazo": {
        "file": os.path.join(ROOT_DIR, "gatazo.csv"),
        "title": "Gatazo",
        "lags": [35, 9, 20, 42, 47, 52, 57, 62],
        "target_streaks": [1],
        "wr_optimos": [0, 1, 3],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": ["11"],
        "markov": {},
        "mirror": {},
        "payout": 60.0,
        "emoji": "🐯"
    },
    "Lotto Activo": {
        "file": os.path.join(ROOT_DIR, "data_vz", "lotto_activo_2anios.csv"),
        "title": "Lotto Activo",
        "lags": [20, 18, 15, 27, 32, 37, 42, 47],
        "target_streaks": [1, 2],
        "wr_optimos": [0, 1, 2],
        "rec_w": 6,
        "anti_clustering": True,
        "blacklist": [],
        "markov": {},
        "mirror": {},
        "payout": 30.0,
        "emoji": "🦁"
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
        "markov": {},
        "mirror": {},
        "payout": 60.0,
        "emoji": "🧘"
    }
}"""

# Reemplazar el bloque RULETAS anterior
pattern = r'RULETAS\s*=\s*\{.*?\n\}'
match = re.search(pattern, code, re.DOTALL)
if match:
    new_code = code[:match.start()] + new_ruletas_block + code[match.end():]
    with open(server_path, 'w', encoding='utf-8') as f:
        f.write(new_code)
    print("server_zero_dep.py actualizado exitosamente con las Top 7 Ruletas a 8 Lags.")
else:
    print("ERROR: No se pudo localizar el bloque RULETAS en server_zero_dep.py")
