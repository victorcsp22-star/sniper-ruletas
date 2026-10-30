"""
========================================================================================
 CONFIGURACIÓN DEL SISTEMA MULTI-RULETA (NUEVAS RULETAS)
========================================================================================
Contiene la definición técnica, matemática y operativa de las ruletas seleccionadas
para operar con ventaja matemática (+EV) bajo la estrategia Gatillo Sniper Post-Fallo 1.
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

# Ruletas aprobadas y configuradas para la Cartera Oficial Unificada (7 Ruletas)
RULETAS_CONFIG = {
    # Núcleo Venezuela (4 Ruletas)
    "Lotto Activo": {
        "file": os.path.join(VZ_DIR, "lotto_activo_2anios.csv"),
        "card_title": "Lotto Activo",
        "lags": [20, 18, 14],
        "target_streaks": [1],
        "rec_w": 6,
        "anti_clustering": True,
        "blacklist": [],
        "markov_snipers": {
            "13": "6",   # MONO -> RANA (EV +90.7%, Z = +3.57)
            "5": "4",    # LEÓN -> ALACRÁN (EV +85.8%, Z = +3.35)
            "14": "22",  # PALOMA -> CAMELLO (EV +80.6%, Z = +3.11)
            "16": "28"   # OSO -> ZAMURO (EV +72.1%, Z = +3.03)
        },
        "payout": 30.0,
        "emoji": "🦁",
        "active": True,
        "f_unit": 0.00900,
        "be_rate": 3.33,
        "grade": "A+ (Núcleo Venezuela - AntiClustering & Markov)"
    },
    "La Granjita": {
        "file": os.path.join(VZ_DIR, "la_granjita_2anios.csv"),
        "card_title": "La Granjita",
        "lags": [15, 17],
        "target_streaks": [1],
        "rec_w": 9,
        "anti_clustering": False,
        "blacklist": [],
        "markov_snipers": {
            "11": "34",  # GATO -> VENADO (EV +109.6%, Z = +4.12)
            "30": "14",  # CAIMÁN -> PALOMA (EV +83.7%, Z = +3.41)
            "26": "15",  # VACA -> ZORRO (EV +82.9%, Z = +3.40)
            "3": "6",    # CIEMPIÉS -> RANA (EV +85.8%, Z = +3.35)
            "24": "16"   # IGUANA -> OSO (EV +72.8%, Z = +3.05)
        },
        "payout": 30.0,
        "emoji": "🐸",
        "active": True,
        "f_unit": 0.00484,
        "be_rate": 3.33,
        "grade": "A+ (Maximizada - Purga Adaptativa Rec9 + Markov)"
    },
    "Ruleta Royal": {
        "file": os.path.join(VZ_DIR, "ruleta_royal_2anios.csv"),
        "card_title": "Ruleta Royal",
        "lags": [16, 19, 31],
        "target_streaks": [1],
        "rec_w": 6,
        "anti_clustering": True,
        "blacklist": [],
        "markov_snipers": {
            "8": "27",   # RATÓN -> PERRO (EV +102.1%, Z = +3.56)
            "3": "16",   # CIEMPIÉS -> OSO (EV +90.2%, Z = +3.32)
            "17": "30",  # PAVO -> CAIMÁN (EV +85.6%, Z = +3.09)
            "26": "9"    # VACA -> ÁGUILA (EV +80.9%, Z = +3.00)
        },
        "payout": 30.0,
        "emoji": "👑",
        "active": True,
        "f_unit": 0.00826,
        "be_rate": 3.33,
        "grade": "A (Núcleo Venezuela - AntiClustering & Markov)"
    },
    "Guacharo Activo": {
        "file": os.path.join(VZ_DIR, "guacharo_activo_2anios.csv"),
        "card_title": "Guacharo",
        "lags": [31, 41, 25, 42, 35],
        "target_streaks": [1],
        "rec_w": 8,
        "anti_clustering": False,
        "blacklist": ["75"],  # Purgado número trampa estadístico Z = -6.40
        "markov_snipers": {
            "37": "15",  # TORTUGA -> ZORRO (EV +218.2%, Z = +4.06, 60x!)
            "59": "57",  # PANTERA -> PATO (EV +255.9%, Z = +4.45, 60x!)
            "16": "39"   # OSO -> LECHUZA (EV +244.3%, Z = +4.33, 60x!)
        },
        "payout": 60.0,
        "emoji": "🦇",
        "active": True,
        "f_unit": 0.00680,
        "be_rate": 1.67,
        "grade": "A+ (Núcleo Venezuela - Purga Rec8 & Markov 60x)"
    },
    # Nuevas Ruletas Validadas (3 Ruletas)
    "Gatazo": {
        "file": os.path.join(BASE_DIR, "gatazo.csv"),
        "card_title": "Gatazo",
        "lags": [35, 9, 20],
        "target_streaks": [1, 2],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": ["11"],  # Purgado número trampa estadístico Z = -5.30
        "markov_snipers": {
            "33": "48",  # PESCADO -> PUERCOESPÍN (EV +900%, Z = +6.09, 60x!)
            "31": "37",  # LAPA -> TORTUGA (EV +900%, Z = +6.09, 60x!)
            "42": "13",  # TUCÁN -> MONO (EV +408.5%, Z = +5.20, 60x!)
            "18": "69",  # BURRO -> CONEJO (EV +445.4%, Z = +4.87, 60x!)
            "30": "63",  # CAIMÁN -> CANGREJO (EV +733.3%, Z = +7.07, 60x!)
            "48": "21"   # PUERCOESPÍN -> GALLO (EV +581.8%, Z = +6.27, 60x!)
        },
        "payout": 60.0,
        "k": 85,
        "emoji": "🐯",
        "active": True,
        "f_unit": 0.00900,
        "be_rate": 1.67,
        "grade": "A+ (Especializada - Doble Gatillo & Hiper-Markov 60x)"
    },
    "Mega Animal 40": {
        "file": os.path.join(BASE_DIR, "mega_animal_40.csv"),
        "card_title": "Mega Animal 40",
        "lags": [18, 21, 20],  # Super-Lag 18 (Z = +6.05)
        "target_streaks": [1],
        "rec_w": 8,
        "anti_clustering": False,
        "blacklist": ["4"],
        "markov_snipers": {
            "32": "35",  # ARDILLA -> JIRAFA (EV +281.8%, Z = +5.45)
            "11": "00",  # GATO -> BALLENA (EV +281.8%, Z = +5.45)
            "25": "32",  # GALLINA -> ARDILLA (EV +185.7%, Z = +4.07)
            "2": "29",   # TORO -> ELEFANTE (EV +350.0%, Z = +3.99)
            "3": "33"    # CIEMPIÉS -> PESCADO (EV +260.0%, Z = +3.42)
        },
        "payout": 30.0,
        "k": 47,
        "emoji": "🦏",
        "active": True,
        "f_unit": 0.00800,
        "be_rate": 3.33,
        "grade": "A+ (Especializada - SuperLag [18,21,20] & Markov)"
    },
    "Monje Millonario": {
        "file": os.path.join(BASE_DIR, "monje_millonario.csv"),
        "card_title": "Monje Millonario",
        "lags": [24, 42],
        "target_streaks": [1],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": ["75"],  # Purgado número límite
        "markov_snipers": {},
        "payout": 60.0,
        "k": 77,
        "emoji": "🧘‍♂️",
        "active": True,
        "f_unit": 0.00700,
        "be_rate": 1.67,
        "grade": "A+ (Especializada - Lags Armónicos [24,42])"
    },
    "Lotto Activo RD Int": {
        "file": os.path.join(BASE_DIR, "lotto_activo_rd_lotoven_completo.csv"),
        "card_title": "Lotto Activo RD Int",
        "lags": [21, 39, 50],
        "target_streaks": [1],
        "payout": 30.0,
        "k": 38,
        "emoji": "🇩🇴",
        "active": False,  # Desactivada de la cartera unificada para evitar lastre de cuota 30x (reserva monorruleta)
        "f_unit": 0.00500,  # 0.50% del bankroll por animal (calibrado para no saturar Circuit Breaker)
        "be_rate": 3.33,
        "min_hour": 11,
        "only_clean_day": True,
        "grade": "AAA (Internacional - Represión Intradía)"
    },
    # Ruletas opcionales / descartadas:
    "Lotto Gato": {
        "file": os.path.join(BASE_DIR, "lotto_gato.csv"),
        "card_title": "Lotto Gato",
        "lags": [19, 38, 16],
        "payout": 30.0,
        "k": 47,
        "emoji": "🐱",
        "active": False,  # Desactivada por defecto (rebote requiere racha 2+)
        "f_unit": 0.00500,
        "be_rate": 3.33,
        "grade": "C (Monitoreo)"
    },
    "Loto Chaima": {
        "file": os.path.join(BASE_DIR, "loto_chaima.csv"),
        "card_title": "Loto Chaima",
        "lags": [35, 29, 38],
        "payout": 40.0,
        "k": 57,
        "emoji": "🦜",
        "active": False,  # Prohibida: -EV verificado
        "f_unit": 0.0,
        "be_rate": 2.50,
        "grade": "DESCARTADA (-EV)"
    }
}

STATE_FILE = os.path.join(BASE_DIR, "state_nuevas_ruletas.json")
LEDGER_FILE = os.path.join(BASE_DIR, "ledger_nuevas_ruletas.csv")
DIARIO_FILE = os.path.join(BASE_DIR, "diario_nuevas_ruletas.md")

# Parámetros del Ciclo de Reinicio Semanal (Retiro Semanal de Ganancias y Stake $1.00 Fijo)
WEEKLY_RESET_ENABLED = True
WEEKLY_CYCLE_DAYS = 7
WEEKLY_KELLY_MULTIPLIER = 0.75  # 0.75x Kelly Base
SIZING_MODEL = "fixed_stake_with_weekly_withdrawals"  # Modelo activo con retiros semanales
FIXED_STAKE_UNIT = 1.00  # $1.00 USD fijo por animalito en cada disparo

# Parámetros Cuantitativos de Control de Riesgo Institucional (Perfil B: Óptimo Balanceado)
TARGET_MDD = 0.32                     # 32% Drawdown objetivo para amortiguación continua de Kelly
MDD_FLOOR = 0.40                      # Piso de drawdown de referencia
WEEKLY_CIRCUIT_BREAKER_PCT = 0.15     # Circuit Breaker semanal: corta al -15% de pérdida en el ciclo
PEAK_DECAY_WEEKS = 12                 # Media-vida del ATH (12 semanas) para evitar parálisis de High-Water Mark
QUARANTINE_MISSES = 20                # Cuarentena preventiva para activos individuales con >= 20 fallos consecutivos

DEFAULT_BANKROLL = 200.0
MIN_BET = 0.10         # Apuesta mínima permitida por animalito

# Módulo de Inversión Inteligente (Rebound Momentum)
SMART_INVESTMENT_ENABLED = True
REBOUND_BOOST_MULTIPLIER = 1.25    # Impulso del +25% en Zona Dulce de Rebote (1 a 3 fallos del gatillo)
FATIGUE_DISCOUNT_MULTIPLIER = 0.85 # Descuento defensivo del 15% en zona fatigada (0 fallos del gatillo)
NEUTRAL_MULTIPLIER = 1.00          # Neutral en el resto de situaciones (>= 4 fallos)
