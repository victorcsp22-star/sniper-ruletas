# Código para alinear server_zero_dep.py exactamente con bot_nuevas_ruletas.py

p_srv = r"C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py"
with open(p_srv, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Eliminar Markov y Espejos de RULETAS y alinear con bot maestro
new_ruletas_dict = '''RULETAS = {
    "Lotto Gato": {
        "file": os.path.join(ROOT_DIR, "lotto_gato.csv"),
        "title": "Lotto Gato",
        "lags": [18, 38, 14],
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
        "lags": [49, 41, 35],
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
        "lags": [31, 54, 41],
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
    "Lotto Activo": {
        "file": os.path.join(ROOT_DIR, "data_vz", "lotto_activo_2anios.csv"),
        "title": "Lotto Activo",
        "lags": [20, 18, 15],
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
    "Ruleta Royal": {
        "file": os.path.join(ROOT_DIR, "data_vz", "ruleta_royal_2anios.csv"),
        "title": "Ruleta Royal",
        "lags": [19, 16, 31],
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
    "Mega Animal 40": {
        "file": os.path.join(ROOT_DIR, "mega_animal_40.csv"),
        "title": "Mega Animal 40",
        "lags": [18, 20, 43],
        "target_streaks": [1, 2, 3],
        "wr_optimos": [1, 2],
        "rec_w": 8,
        "anti_clustering": False,
        "blacklist": ["4"],
        "markov": {},
        "mirror": {},
        "payout": 30.0,
        "emoji": "🦏"
    },
    "Gatazo": {
        "file": os.path.join(ROOT_DIR, "gatazo.csv"),
        "title": "Gatazo",
        "lags": [35, 9, 20],
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
    "Monje Millonario": {
        "file": os.path.join(ROOT_DIR, "monje_millonario.csv"),
        "title": "Monje Millonario",
        "lags": [24, 42, 48],
        "target_streaks": [0, 1],
        "wr_optimos": [0, 1],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": ["75"],
        "markov": {},
        "mirror": {},
        "payout": 60.0,
        "emoji": "🧘"
    },
    "Granja Millonaria - Granjazo": {
        "file": os.path.join(ROOT_DIR, "granja_millonaria_granjazo.csv"),
        "title": "Granjazo",
        "lags": [45, 26, 15],
        "target_streaks": [1, 3],
        "wr_optimos": [0, 1],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": [],
        "markov": {},
        "mirror": {},
        "payout": 60.0,
        "emoji": "🚜"
    }
}'''

# Reemplazar RULETAS en el código
idx1 = code.find('RULETAS = {')
idx2 = code.find('def get_ruleta_filepath(r_name):')
if idx1 != -1 and idx2 != -1:
    code = code[:idx1] + new_ruletas_dict + '\n\n\n' + code[idx2:]
    print("RULETAS actualizado con exito")
else:
    print("No se encontro seccion RULETAS")

with open(p_srv, 'w', encoding='utf-8') as f:
    f.write(code)
print("Archivo server_zero_dep.py guardado")
