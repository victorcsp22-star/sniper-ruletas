import os
import sys
import json
import shutil
import pandas as pd
from datetime import datetime, timedelta

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = r"C:\Users\victo\nuevas_ruletas"
VZ_DIR = os.path.join(ROOT_DIR, "data_vz")

RULETAS_CONFIG = {
    "Lotto Activo": {
        "file": os.path.join(VZ_DIR, "lotto_activo_2anios.csv"),
        "lags": [20, 18, 14],
        "target_streaks": [1],
        "rec_w": 6,
        "anti_clustering": True,
        "payout": 30.0,
        "f_unit": 0.00900,
        "k": 38,
        "emoji": "🦁"
    },
    "La Granjita": {
        "file": os.path.join(VZ_DIR, "la_granjita_2anios.csv"),
        "lags": [15, 17],
        "target_streaks": [1],
        "rec_w": 9,
        "anti_clustering": False,
        "payout": 30.0,
        "f_unit": 0.00484,
        "k": 38,
        "emoji": "🐸"
    },
    "Ruleta Royal": {
        "file": os.path.join(VZ_DIR, "ruleta_royal_2anios.csv"),
        "lags": [16, 19, 31],
        "target_streaks": [1],
        "rec_w": 6,
        "anti_clustering": True,
        "payout": 30.0,
        "f_unit": 0.00826,
        "k": 38,
        "emoji": "👑"
    },
    "Guacharo Activo": {
        "file": os.path.join(VZ_DIR, "guacharo_activo_2anios.csv"),
        "lags": [31, 41, 25, 42, 35],
        "target_streaks": [1],
        "rec_w": 8,
        "anti_clustering": False,
        "payout": 60.0,
        "f_unit": 0.00680,
        "k": 77,
        "emoji": "🦇"
    },
    "Gatazo": {
        "file": os.path.join(ROOT_DIR, "gatazo.csv"),
        "lags": [35, 22, 20],
        "target_streaks": [1, 2],
        "rec_w": 6,
        "anti_clustering": False,
        "payout": 60.0,
        "f_unit": 0.00900,
        "k": 85,
        "emoji": "🐯"
    },
    "Mega Animal 40": {
        "file": os.path.join(ROOT_DIR, "mega_animal_40.csv"),
        "lags": [18, 21, 20],
        "target_streaks": [1],
        "rec_w": 8,
        "anti_clustering": False,
        "payout": 30.0,
        "f_unit": 0.00800,
        "k": 47,
        "emoji": "🦏"
    },
    "Monje Millonario": {
        "file": os.path.join(ROOT_DIR, "monje_millonario.csv"),
        "lags": [24, 42],
        "target_streaks": [1],
        "rec_w": 6,
        "anti_clustering": False,
        "payout": 60.0,
        "f_unit": 0.00700,
        "k": 77,
        "emoji": "🧘‍♂️"
    }
}

START_DT = datetime(2026, 10, 17, 9, 47, 0)
print(f"Punto de Inicio: {START_DT}")

for r_name, cfg in RULETAS_CONFIG.items():
    df = pd.read_csv(cfg["file"], dtype={"numero": str})
    df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
    sub = df[df["sort_dt"] >= START_DT]
    print(f"{r_name}: {len(sub)} sorteos desde el 17-Oct 09:47 AM. Último: {sub.iloc[-1]['fecha']} {sub.iloc[-1]['hora']} (#{sub.iloc[-1]['numero']} {sub.iloc[-1]['animal']})")
