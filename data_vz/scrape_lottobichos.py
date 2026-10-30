"""
========================================================================================
 SCRAPER DEDICADO: LOTTO BRASIL Y LOTTO BICHO (ISOLADO / SANDBOX)
========================================================================================
Descarga el historial oficial de 2 años (2024-10-14 al 2026-10-14) desde lottobichos.com
Genera datasets limpios y compatibles:
 - lottobrasil_2anios.csv
 - lottobicho_2anios.csv
========================================================================================
"""

import datetime
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import requests

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_URL = "https://lottobichos.com/sorteios/getsorteios"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}

DIAS_ES = {
    0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves",
    4: "Viernes", 5: "Sábado", 6: "Domingo"
}

HORAS_MAP = {
    "H_08": "8:00 AM",
    "H_09": "9:00 AM",
    "H_10": "10:00 AM",
    "H_11": "11:00 AM",
    "H_12": "12:00 PM",
    "H_13": "1:00 PM",
    "H_14": "2:00 PM",
    "H_15": "3:00 PM",
    "H_16": "4:00 PM",
    "H_17": "5:00 PM",
    "H_18": "6:00 PM",
    "H_19": "7:00 PM",
}

# Animal mappings
ANIMALS_BASE = [
    'GOLFINHO', 'FLAMENCO', 'TOURO', 'LACRAIA', 'ESCORPIÃO', 'LEÃO', 'SAPO',
    'PERIQUITO', 'RATO', 'ARARA', 'TIGRE', 'GATO', 'CAVALO', 'MACACO',
    'POMBA', 'RAPOSA', 'URSO', 'PERU', 'BURRO', 'CABRA', 'PORCO',
    'GALO', 'CAMELO', 'ZEBRA', 'IGUANA', 'GALINHA', 'VACA', 'CACHORRO',
    'ABUTRE', 'ELEFANTE', 'JACARÉ', 'CAPIVARA', 'ESQUILO', 'PEIXE',
    'VEADO', 'GIRAFA', 'COBRA'
]

MAP_BRASIL = {}
MAP_BICHO = {}

# Map 0 -> GOLFINHO
MAP_BRASIL["0"] = "GOLFINHO"
MAP_BICHO["0"] = "GOLFINHO"

for i in range(1, 37):
    num_str = f"{i:02d}"
    MAP_BRASIL[num_str] = "CORUJA" if i == 9 else ANIMALS_BASE[i]
    MAP_BICHO[num_str] = ANIMALS_BASE[i]

MAP_BRASIL["00"] = "BALEIA"
MAP_BICHO["00"] = "BALEIA"


def fetch_day(args):
    cur_date, lotr_code = args
    d_str = cur_date.strftime("%d-%m-%Y")
    for attempt in range(3):
        try:
            r = requests.post(API_URL, data={"date": d_str, "lotr": lotr_code}, headers=HEADERS, timeout=8)
            if r.status_code == 200:
                js = r.json()
                if js.get("status"):
                    data = js.get("data", {})
                    # The response object has key 'tuan' for lottbrasil or 'bicho' for bicho
                    key = list(data.keys())[0] if data else None
                    if key:
                        return cur_date, data[key]
            elif r.status_code == 500:
                # No data for this date
                return cur_date, {}
        except Exception:
            time.sleep(0.5)
    return cur_date, {}


def scrape_lottery(lotr_code: str, lotr_name: str, out_csv: str, start_date: datetime.date, end_date: datetime.date):
    print(f"\n{'='*70}")
    print(f"Iniciando descarga de {lotr_name} ({lotr_code})")
    print(f"Rango: {start_date} al {end_date} ({(end_date - start_date).days + 1} días)")
    print(f"{'='*70}")

    total_days = (end_date - start_date).days + 1
    dates = [start_date + datetime.timedelta(days=i) for i in range(total_days)]
    tasks = [(d, lotr_code) for d in dates]

    records = []
    animal_map = MAP_BRASIL if lotr_code == "lottbrasil" else MAP_BICHO

    completed = 0
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_task = {executor.submit(fetch_day, t): t for t in tasks}
        for future in as_completed(future_to_task):
            completed += 1
            if completed % 100 == 0 or completed == total_days:
                elapsed = time.time() - t0
                print(f"  Progreso: {completed}/{total_days} días completados ({completed/total_days*100:.1f}%) - {elapsed:.1f}s")
            
            cur_date, day_data = future.result()
            if not day_data:
                continue

            for h_code in sorted(HORAS_MAP.keys()):
                val = day_data.get(h_code)
                if val and val != '--':
                    # Clean number
                    val_clean = str(val).strip()
                    hora_clean = HORAS_MAP[h_code]
                    dia_semana = DIAS_ES[cur_date.weekday()]
                    animal_clean = animal_map.get(val_clean, "DESCONOCIDO")

                    records.append({
                        "fecha": cur_date.strftime("%Y-%m-%d"),
                        "dia": dia_semana,
                        "hora": hora_clean,
                        "numero": val_clean,
                        "animal": animal_clean,
                        "loteria": lotr_name,
                        # auxiliary for sorting
                        "_sort_key": f"{cur_date.strftime('%Y-%m-%d')}_{h_code}"
                    })

    df = pd.DataFrame(records)
    if df.empty:
        print(f"ADVERTENCIA: No se recuperaron registros para {lotr_name}")
        return

    # Sort strictly chronologically
    df = df.sort_values(by="_sort_key").drop(columns=["_sort_key"])
    df.to_csv(out_csv, index=False, encoding="utf-8")
    
    print(f"\n--> EXPORTACIÓN EXITOSA:")
    print(f"    Archivo: {out_csv}")
    print(f"    Total sorteos: {len(df):,}")
    print(f"    Días únicos con sorteos: {df['fecha'].nunique():,}")
    print(f"    Fecha inicio: {df['fecha'].min()} | Fecha fin: {df['fecha'].max()}")
    print(f"    Números únicos observados: {df['numero'].nunique()} / 38")
    print(f"    Muestra de los primeros 5 sorteos:\n{df.head(5).to_string(index=False)}")


if __name__ == "__main__":
    start = datetime.date(2024, 10, 14)
    end = datetime.date(2026, 10, 14)

    scrape_lottery("lottbrasil", "Lotto Brasil", os.path.join(BASE_DIR, "lottobrasil_2anios.csv"), start, end)
    scrape_lottery("bicho", "Lotto Bicho", os.path.join(BASE_DIR, "lottobicho_2anios.csv"), start, end)
