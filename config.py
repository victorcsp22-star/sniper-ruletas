"""
========================================================================================
 CONFIGURACIÓN DEL SISTEMA MULTI-RULETA (CARTERA ÉLITE DE 9 RULETAS)
========================================================================================
Contiene la definición técnica, matemática y operativa de las 9 ruletas seleccionadas
para operar con ventaja matemática (+EV) bajo la supervisión de Agentes Especializados
con detección de patrones, canales de Markov e hiper-espejos.
========================================================================================
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SEMANA_URL = "https://www.tuazar.com/loteria/animalitos/resultados/semana/"
BASE_TUAZAR_URL = "https://www.tuazar.com/loteria/animalitos/resultados/"

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

VZ_DIR = os.path.join(BASE_DIR, "data_vz")

# CARTERA ÉLITE OFICIAL (9 RULETAS SELECCIONADAS)
RULETAS_CONFIG = {
    # 1. Lotto Gato (Máxima rentabilidad del portafolio)
    "Lotto Gato": {
        "file": os.path.join(BASE_DIR, "lotto_gato.csv"),
        "card_title": "Lotto Gato",
        "lags": [18, 38, 14, 25, 30, 35, 40, 45],
        "target_streaks": [1, 2],
        "wr_optimos": [1, 2],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": [],
        "markov_snipers": {
            "14": "0",   # PALOMA -> DELFÍN (Lift 8.54x)
            "27": "15",  # PERRO -> ZORRO (Lift 7.72x)
            "3": "7"     # CIEMPIÉS -> PERICO (Lift 7.61x)
        },
        "mirror_pairs": {
            "0": "00", "1": "10", "2": "20", "3": "30", "4": "40"
        },
        "payout": 60.0,
        "emoji": "🐱",
        "active": True,
        "f_unit": 0.00900,
        "be_rate": 1.67,
        "grade": "AAA (Suprema - ROI +159% & Markov 60x)"
    },

    # 2. Loto Chaima (Pilar de volumen 60x en 9,000 sorteos)
    "Loto Chaima": {
        "file": os.path.join(BASE_DIR, "loto_chaima.csv"),
        "card_title": "Loto Chaima",
        "lags": [49, 41, 35, 56, 61, 66, 71, 76],
        "target_streaks": [0, 1],
        "wr_optimos": [0, 1],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": [],
        "markov_snipers": {
            "48": "0",   # PUERCOESPÍN -> DELFÍN (Lift 5.92x)
            "55": "0",   # ZORRO/ANIMAL -> DELFÍN (Lift 5.31x)
            "12": "0"    # CABALLO -> DELFÍN (Lift 4.78x)
        },
        "mirror_pairs": {
            "0": "00", "5": "50", "6": "60", "7": "70"
        },
        "payout": 60.0,
        "emoji": "🏹",
        "active": True,
        "f_unit": 0.00850,
        "be_rate": 1.67,
        "grade": "AAA (Sólida - 9,000 sorteos & Atractor Delfín)"
    },

    # 3. Guacharo Activo (Pilar histórico de 9,000 sorteos)
    "Guacharo Activo": {
        "file": os.path.join(VZ_DIR, "guacharo_activo_2anios.csv"),
        "card_title": "Guacharo",
        "lags": [31, 54, 41, 38, 43, 48, 53, 58],
        "target_streaks": [1, 3],
        "wr_optimos": [1, 3, 6],
        "rec_w": 8,
        "anti_clustering": False,
        "blacklist": ["75"],
        "markov_snipers": {
            "21": "0",   # GALLO -> DELFÍN (Lift 4.69x)
            "8": "67",   # RATÓN -> AVESTRUZ (Lift 4.61x)
            "29": "2"    # ELEFANTE -> TORO (Lift 4.57x)
        },
        "mirror_pairs": {
            "12": "21", "13": "31", "14": "41", "23": "32"
        },
        "payout": 60.0,
        "emoji": "🦇",
        "active": True,
        "f_unit": 0.00750,
        "be_rate": 1.67,
        "grade": "AAA (Histórica - Purga Rec8 & Markov 60x)"
    },

    # 4. Lotto Activo (Clásica de alta estabilidad y volumen)
    "Lotto Activo": {
        "file": os.path.join(VZ_DIR, "lotto_activo_2anios.csv"),
        "card_title": "Lotto Activo",
        "lags": [20, 18, 15, 27, 32, 37, 42, 47],
        "target_streaks": [1, 2],
        "wr_optimos": [0, 1, 2],
        "rec_w": 6,
        "anti_clustering": True,
        "blacklist": [],
        "markov_snipers": {
            "14": "0",   # PALOMA -> DELFÍN (Lift 2.99x)
            "31": "0",   # LAPA -> DELFÍN (Lift 2.90x)
            "6": "0"     # RANA -> DELFÍN (Lift 2.90x)
        },
        "mirror_pairs": {
            "12": "21", "13": "31", "23": "32", "0": "00"
        },
        "payout": 30.0,
        "emoji": "🦁",
        "active": False,
        "f_unit": 0.00900,
        "be_rate": 3.33,
        "grade": "AA+ (Núcleo Tradicional - Anti-Clustering Activo)"
    },

    # 5. Ruleta Royal (Excelente win rate y consistencia)
    "Ruleta Royal": {
        "file": os.path.join(VZ_DIR, "ruleta_royal_2anios.csv"),
        "card_title": "Ruleta Royal",
        "lags": [19, 16, 31, 26, 31, 36, 41, 46],
        "target_streaks": [1],
        "wr_optimos": [0, 1, 6],
        "rec_w": 6,
        "anti_clustering": True,
        "blacklist": [],
        "markov_snipers": {
            "25": "22",  # GALLINA -> CAMELLO (Lift 2.56x)
            "8": "27"    # RATÓN -> PERRO (Lift 2.56x)
        },
        "mirror_pairs": {
            "12": "21", "13": "31", "23": "32"
        },
        "payout": 30.0,
        "emoji": "👑",
        "active": False,
        "f_unit": 0.00850,
        "be_rate": 3.33,
        "grade": "AA+ (Consistencia - Anti-Clustering & Markov)"
    },

    # 6. Mega Animal 40 (Menor volatilidad y drawdown mínimo del sistema)
    "Mega Animal 40": {
        "file": os.path.join(BASE_DIR, "mega_animal_40.csv"),
        "card_title": "Mega Animal 40",
        "lags": [18, 20, 43],
        "target_streaks": [1, 2, 3],
        "wr_optimos": [0, 1, 2, 3],
        "rec_w": 8,
        "anti_clustering": False,
        "blacklist": ["4"],
        "markov_snipers": {
            "30": "0",   # CAIMÁN -> DELFÍN (Lift 5.90x)
            "11": "0",   # GATO -> DELFÍN (Lift 5.82x)
            "32": "35"   # ARDILLA -> JIRAFA (Lift 5.00x)
        },
        "mirror_pairs": {
            "11": "00", "12": "21", "13": "31", "23": "32"
        },
        "payout": 30.0,
        "emoji": "🦏",
        "active": False,
        "f_unit": 0.00800,
        "be_rate": 3.33,
        "grade": "AAA (Ancla Defensiva - Drawdown mínimo $46)"
    },

    # 7. Gatazo (Captura de cuotas 60x y anomalías Markov extremas)
    "Gatazo": {
        "file": os.path.join(BASE_DIR, "gatazo.csv"),
        "card_title": "Gatazo",
        "lags": [35, 9, 20, 42, 47, 52, 57, 62],
        "target_streaks": [1],
        "wr_optimos": [1, 11, 12],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": ["11"],
        "markov_snipers": {
            "30": "63",  # CAIMÁN -> CANGREJO (Lift 10.42x)
            "48": "21",  # PUERCOESPÍN -> GALLO (Lift 8.52x)
            "23": "42"   # CEBRA -> TUCÁN (Lift 8.15x)
        },
        "mirror_pairs": {
            "12": "21", "13": "31", "24": "42", "34": "43"
        },
        "payout": 60.0,
        "emoji": "🐯",
        "active": True,
        "f_unit": 0.00900,
        "be_rate": 1.67,
        "grade": "AA+ (Asimétrica - Hiper-Markov 10.4x)"
    },

    # 8. Monje Millonario (Francotirador de Racha 0 a 60x)
    "Monje Millonario": {
        "file": os.path.join(BASE_DIR, "monje_millonario.csv"),
        "card_title": "Monje Millonario",
        "lags": [24, 42, 48, 31, 36, 41, 46, 51],
        "target_streaks": [0, 1],
        "wr_optimos": [0, 1],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": ["75"],
        "markov_snipers": {},
        "mirror_pairs": {
            "24": "42"
        },
        "payout": 60.0,
        "emoji": "🧘‍♂️",
        "active": True,
        "f_unit": 0.00700,
        "be_rate": 1.67,
        "grade": "A (Francotirador Cuota 60x - Racha 0-1)"
    },

    # 9. Granja Millonaria - Granjazo (Alta asimetría de cuota 60x)
    "Granja Millonaria - Granjazo": {
        "file": os.path.join(BASE_DIR, "granja_millonaria_granjazo.csv"),
        "card_title": "Granjazo",
        "lags": [45, 26, 15],
        "target_streaks": [1, 3],
        "wr_optimos": [1, 3],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": [],
        "markov_snipers": {},
        "mirror_pairs": {
            "15": "51", "26": "62"
        },
        "payout": 60.0,
        "emoji": "🚜",
        "active": True,
        "f_unit": 0.00700,
        "be_rate": 1.67,
        "grade": "A (Promesa 60x - ROI +100%)"
    },

    # Ruletas en Reserva (Desactivadas de la Cartera Oficial)
    "La Granjita": {
        "file": os.path.join(VZ_DIR, "la_granjita_2anios.csv"),
        "card_title": "La Granjita",
        "lags": [15, 40, 41],
        "target_streaks": [2, 3],
        "payout": 30.0,
        "emoji": "🐸",
        "active": False,  # Expulsada: -EV en Racha 1 (-8.88% ROI y DD -$331)
        "grade": "RESERVA (Condicionada a Racha 2-3)"
    },
    "Lotto Activo RD Int": {
        "file": os.path.join(BASE_DIR, "lotto_activo_rd_lotoven_completo.csv"),
        "card_title": "Lotto Activo RD Int",
        "lags": [21, 39, 50],
        "payout": 30.0,
        "emoji": "🇩🇴",
        "active": False,  # Desactivada para evitar canibalización con Lotto Activo
        "grade": "RESERVA"
    }
}

STATE_FILE = os.path.join(BASE_DIR, "state_nuevas_ruletas.json")
LEDGER_FILE = os.path.join(BASE_DIR, "ledger_nuevas_ruletas.csv")
DIARIO_FILE = os.path.join(BASE_DIR, "diario_nuevas_ruletas.md")

# Parámetros del Ciclo de Reinicio Semanal
WEEKLY_RESET_ENABLED = True
WEEKLY_CYCLE_DAYS = 7
WEEKLY_KELLY_MULTIPLIER = 0.75
SIZING_MODEL = "fixed_stake_with_weekly_withdrawals"
FIXED_STAKE_UNIT = 1.00

# Parámetros de Riesgo Institucional
TARGET_MDD = 0.32
MDD_FLOOR = 0.40
WEEKLY_CIRCUIT_BREAKER_PCT = 0.15
PEAK_DECAY_WEEKS = 12
QUARANTINE_MISSES = 20

DEFAULT_BANKROLL = 200.0
MIN_BET = 0.10

# Inversión Inteligente
SMART_INVESTMENT_ENABLED = True
REBOUND_BOOST_MULTIPLIER = 1.25
FATIGUE_DISCOUNT_MULTIPLIER = 0.85
NEUTRAL_MULTIPLIER = 1.00
