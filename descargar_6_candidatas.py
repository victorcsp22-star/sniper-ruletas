"""
========================================================================================
 DESCARGADOR DE 2 AÑOS: CHANCE A, CHANCE B, EL ARREJUNTAO, BICHITOS, FIERAS, MASCOTAS
========================================================================================
Descarga el historial de 104 semanas (2 años: Noviembre 2024 a Noviembre 2026) 
directamente de TuAzar usando su endpoint de semanas anteriores.
========================================================================================
"""

import concurrent.futures
import datetime
import os
import sys
import time
from typing import Dict, List, Optional
import lxml.html
import pandas as pd
import requests

OUTPUT_DIR = r"C:\Users\victo\nuevas_ruletas\data_candidatos"
os.makedirs(OUTPUT_DIR, exist_ok=True)

BASE_URL = "https://www.tuazar.com/loteria/animalitos/resultados/"
ANTERIORES_URL = BASE_URL + "anteriores/{date}/"
SEMANA_URL = BASE_URL + "semana/"

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
    0: "Lunes",
    1: "Martes",
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo"
}

# Mapeo exacto de los nombres en TuAzar a nombres de archivo
TARGETS_MAP = {
    "Chance Con Animalitos A": "chance_con_animalitos_a.csv",
    "Chance Con Animalitos B": "chance_con_animalitos_b.csv",
    "El Arrejuntao": "el_arrejuntao.csv",
    "Animalitos del Oriente - Bichitos": "bichitos.csv",
    "Animalitos del Oriente - Fieras": "fieras.csv",
    "Animalitos del Oriente - Mascotas": "mascotas.csv"
}

def clean_animal_name(name: str) -> str:
    if not isinstance(name, str):
        return ""
    name = name.strip()
    exact_map = {
        "AGUILA": "ÁGUILA",
        "ALACRAN": "ALACRÁN",
        "CAIMAN": "CAIMÁN",
        "CIEMPIES": "CIEMPIÉS",
        "DELFIN": "DELFÍN",
        "LEON": "LEÓN",
        "RATON": "RATÓN",
        "TIBURON": "TIBURÓN",
        "TUCAN": "TUCÁN",
        "BUFALO": "BÚFALO",
        "CHUGUIRE": "CHIGÜIRE",
        "PUERCOESPIN": "PUERCOESPÍN",
        "CAMALEON": "CAMALEÓN",
        "GAVILAN": "GAVILÁN",
        "HIPOPOTAMO": "HIPOPÓTAMO",
        "ARANA": "ARAÑA",
    }
    return exact_map.get(name, name)

def parse_date_dmy(dmy_str: str) -> Optional[datetime.date]:
    try:
        parts = dmy_str.strip().split('/')
        if len(parts) == 3:
            return datetime.date(int(parts[2]), int(parts[1]), int(parts[0]))
    except Exception:
        pass
    return None

def extract_targets_from_html(html_content: str, targets: List[str]) -> Dict[str, List[Dict]]:
    res = {t: [] for t in targets}
    try:
        doc = lxml.html.fromstring(html_content)
    except Exception:
        return res

    cards = doc.xpath('//div[contains(@class, "lw-card")]')

    for card in cards:
        title_el = card.xpath('.//h3[contains(@class, "lw-title")]')
        if not title_el:
            continue
        card_title = title_el[0].text_content().strip()
        
        matched_target = None
        for t in targets:
            if t.lower() in card_title.lower():
                matched_target = t
                break
                
        if not matched_target:
            continue

        table = card.xpath('.//table[contains(@class, "lw-table")]')
        if not table:
            continue
        table = table[0]

        day_headers = table.xpath('.//thead//th[contains(@class, "lw-day")]')
        column_dates: List[Optional[datetime.date]] = []
        for th in day_headers:
            day_num_el = th.xpath('.//span[contains(@class, "lw-day-num")]')
            if day_num_el:
                column_dates.append(parse_date_dmy(day_num_el[0].text_content()))
            else:
                column_dates.append(None)

        rows = table.xpath('.//tbody/tr')
        for row in rows:
            time_el = row.xpath('.//th[contains(@class, "lw-time")]')
            draw_time = time_el[0].text_content().strip() if time_el else ""

            cells = row.xpath('.//td')
            for dt, cell in zip(column_dates, cells):
                if dt is None:
                    continue
                num_el = cell.xpath('.//span[@class="lw-animal-num"]')
                animal_el = cell.xpath('.//span[@class="lw-animal"]')

                if num_el and animal_el:
                    numero = num_el[0].text_content().strip()
                    animal = clean_animal_name(animal_el[0].text_content().strip())
                    if numero and animal and numero != "-":
                        res[matched_target].append({
                            "fecha": dt.strftime("%Y-%m-%d"),
                            "dia": DIAS_MAP.get(dt.weekday(), ""),
                            "hora": draw_time,
                            "numero": str(numero),
                            "animal": str(animal),
                            "loteria": matched_target
                        })
    return res

def get_previous_sundays(start_date: datetime.date, end_date: datetime.date) -> List[datetime.date]:
    current = end_date
    while current.weekday() != 6:
        current -= datetime.timedelta(days=1)
    sundays = []
    while current >= start_date:
        sundays.append(current)
        current -= datetime.timedelta(days=7)
    return sundays

def fetch_week(sunday_date: datetime.date, session: requests.Session) -> Dict[str, List[Dict]]:
    url = ANTERIORES_URL.format(date=sunday_date.strftime("%Y-%m-%d"))
    for attempt in range(3):
        try:
            resp = session.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                return extract_targets_from_html(resp.text, list(TARGETS_MAP.keys()))
            elif resp.status_code == 404:
                return {t: [] for t in TARGETS_MAP}
        except Exception:
            time.sleep(1)
    return {t: [] for t in TARGETS_MAP}

def main():
    print("=" * 80)
    print("INICIANDO DESCARGA DE 2 AÑOS PARA LAS 6 RULETAS CANDIDATAS:")
    for k, v in TARGETS_MAP.items():
        print(f"  - {k} -> {v}")
    print("=" * 80)

    # 104 semanas = 2 años (desde Nov 2024 hasta Nov 2026)
    end_date = datetime.date(2026, 11, 1)
    start_date = end_date - datetime.timedelta(days=730)
    
    sundays = get_previous_sundays(start_date, end_date)
    print(f"Total de domingos (semanas) a consultar: {len(sundays)}")

    all_data = {t: [] for t in TARGETS_MAP}

    # Descargar semana en curso primero
    session = requests.Session()
    try:
        resp = session.get(SEMANA_URL, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            current_week_data = extract_targets_from_html(resp.text, list(TARGETS_MAP.keys()))
            for t, rows in current_week_data.items():
                all_data[t].extend(rows)
            print("[+] Semana actual descargada.")
    except Exception as e:
        print(f"[!] Error descargando semana actual: {e}")

    # Descarga concurrente con ThreadPoolExecutor (8 hilos seguros)
    completed = 0
    total = len(sundays)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_date = {executor.submit(fetch_week, s, session): s for s in sundays}
        for future in concurrent.futures.as_completed(future_to_date):
            d = future_to_date[future]
            completed += 1
            try:
                res_dict = future.result()
                for t, rows in res_dict.items():
                    all_data[t].extend(rows)
                if completed % 15 == 0 or completed == total:
                    print(f"[*] Progreso: {completed}/{total} semanas procesadas ({(completed/total)*100:.1f}%)")
            except Exception as e:
                print(f"[!] Fallo semana {d}: {e}")

    print("\n" + "=" * 80)
    print("RESUMEN DE SORTEOS HISTÓRICOS DESCARGADOS:")
    print("=" * 80)
    for target, filename in TARGETS_MAP.items():
        rows = all_data[target]
        if not rows:
            print(f"[-] {target}: 0 sorteos encontrados (posiblemente ruleta nueva o sin histórico antiguo).")
            continue
        
        df = pd.DataFrame(rows)
        # Eliminar duplicados
        df.drop_duplicates(subset=["fecha", "hora"], keep="first", inplace=True)
        # Ordenar cronológicamente
        df.sort_values(by=["fecha", "hora"], inplace=True)
        
        out_path = os.path.join(OUTPUT_DIR, filename)
        df.to_csv(out_path, index=False, encoding="utf-8")
        min_date = df["fecha"].min()
        max_date = df["fecha"].max()
        print(f"[+] {target}: {len(df):,} sorteos guardados en '{filename}' | Rango: {min_date} a {max_date}")

if __name__ == "__main__":
    main()
