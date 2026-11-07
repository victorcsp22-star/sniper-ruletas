"""
CONFIGURACIÓN DE REFERENCIA (BASELINE PREVIO)
Utilizada por bot_referencia_baseline.py para correr en paralelo en la PC
y permitir la comparación en tiempo real contra el bot principal.
"""

import os

BASE_DIR = r"C:\Users\victo\nuevas_ruletas"
VZ_DIR = os.path.join(BASE_DIR, "data_vz")

STATE_FILE = os.path.join(BASE_DIR, "state_referencia_baseline.json")
LEDGER_FILE = os.path.join(BASE_DIR, "ledger_referencia_baseline.csv")
DIARIO_FILE = os.path.join(BASE_DIR, "diario_referencia_baseline.md")

BASE_TUAZAR_URL = "https://www.tuazar.com/loteria/animalitos/resultados/"
SEMANA_URL = "https://www.tuazar.com/loteria/animalitos/resultados/semana/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

DEFAULT_BANKROLL = 200.0
FIXED_STAKE_UNIT = 1.0
MIN_BET = 1.0
MDD_FLOOR = 0.10
PEAK_DECAY_WEEKS = 4
QUARANTINE_MISSES = 8
REBOUND_BOOST_MULTIPLIER = 1.30
FATIGUE_DISCOUNT_MULTIPLIER = 0.50
NEUTRAL_MULTIPLIER = 1.00

DIAS_MAP = {
    0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves",
    4: "Viernes", 5: "Sábado", 6: "Domingo"
}

# CARTERA BASELINE DE REFERENCIA
RULETAS_CONFIG = {
    "Mega Animal 40": {
        "file": os.path.join(BASE_DIR, "mega_animal_40.csv"),
        "card_title": "Mega Animal 40",
        "lags": [18, 21, 20],
        "target_streaks": [1, 2, 3],
        "wr_optimos": [1, 2, 3],
        "rec_w": 8,
        "anti_clustering": False,
        "blacklist": ["4"],
        "payout": 30.0,
        "emoji": "🦏",
        "active": True,
        "f_unit": 0.00800
    },
    "Gatazo": {
        "file": os.path.join(BASE_DIR, "gatazo.csv"),
        "card_title": "Gatazo",
        "lags": [35, 22, 20],
        "target_streaks": [1, 2],
        "wr_optimos": [1, 2],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": ["11"],
        "payout": 60.0,
        "emoji": "🐯",
        "active": True,
        "f_unit": 0.00900
    },
    "Monje Millonario": {
        "file": os.path.join(BASE_DIR, "monje_millonario.csv"),
        "card_title": "Monje Millonario",
        "lags": [24, 42],
        "target_streaks": [0, 1],
        "wr_optimos": [0, 1],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": ["75"],
        "payout": 60.0,
        "emoji": "🧘‍♂️",
        "active": True,
        "f_unit": 0.00700
    },
    "Lotto Activo": {
        "file": os.path.join(VZ_DIR, "lotto_activo_2anios.csv"),
        "card_title": "Lotto Activo",
        "lags": [20, 18, 14],
        "target_streaks": [1, 2],
        "wr_optimos": [1, 2],
        "rec_w": 6,
        "anti_clustering": True,
        "blacklist": [],
        "payout": 30.0,
        "emoji": "🦁",
        "active": True,
        "f_unit": 0.00900
    },
    "Ruleta Royal": {
        "file": os.path.join(VZ_DIR, "ruleta_royal_2anios.csv"),
        "card_title": "Ruleta Royal",
        "lags": [16, 19, 31],
        "target_streaks": [1],
        "wr_optimos": [1],
        "rec_w": 6,
        "anti_clustering": True,
        "blacklist": [],
        "payout": 30.0,
        "emoji": "👑",
        "active": True,
        "f_unit": 0.00850
    },
    "Guacharo Activo": {
        "file": os.path.join(VZ_DIR, "guacharo_activo_2anios.csv"),
        "card_title": "Guacharo",
        "lags": [31, 41, 25, 42, 35],
        "target_streaks": [1, 3],
        "wr_optimos": [1, 3],
        "rec_w": 8,
        "anti_clustering": False,
        "blacklist": ["75"],
        "payout": 60.0,
        "emoji": "🦇",
        "active": True,
        "f_unit": 0.00750
    },
    "Lotto Gato": {
        "file": os.path.join(BASE_DIR, "lotto_gato.csv"),
        "card_title": "Lotto Gato",
        "lags": [18, 38, 16],
        "target_streaks": [1, 2],
        "wr_optimos": [1, 2],
        "rec_w": 8,
        "anti_clustering": True,
        "blacklist": [],
        "payout": 30.0,
        "emoji": "🐱",
        "active": True,
        "f_unit": 0.00850
    },
    "Granja Millonaria - Granjazo": {
        "file": os.path.join(BASE_DIR, "granja_millonaria_granjazo.csv"),
        "card_title": "Granja Millonaria - Granjazo",
        "lags": [45, 26, 15],
        "target_streaks": [1],
        "wr_optimos": [1],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": [],
        "payout": 60.0,
        "emoji": "🚜",
        "active": True,
        "f_unit": 0.00800
    }
}

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
