"""
Descargador general y actualizador a 2 años de las ruletas de TuAzar solicitadas.
Objetivos:
1. Tropi Gana (completamente nueva)
2. Selva Plus (ampliar historial hacia atrás si existe)
3. Granja Millonaria - Granjazo (ampliar historial si existe)
4. Granja Millonaria - Animalitos (ampliar historial si existe)
5. El Guacharito Millonario (actualizar del 15-oct al 31-oct)
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

OUTPUT_DIR = r"C:\Users\victo\nuevas_ruletas"
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
    0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves",
    4: "Viernes", 5: "Sábado", 6: "Domingo"
}

TARGETS_MAP = {
    "Tropi Gana": os.path.join(OUTPUT_DIR, "tropi_gana.csv"),
    "Selva Plus": os.path.join(OUTPUT_DIR, "data_vz", "selva_plus_2anios.csv"),
    "Granja Millonaria - Granjazo": os.path.join(OUTPUT_DIR, "granja_millonaria_granjazo.csv"),
    "Granja Millonaria - Animalitos": os.path.join(OUTPUT_DIR, "granja_millonaria_animalitos.csv"),
    "El Guacharito Millonario": os.path.join(OUTPUT_DIR, "data_vz", "guacharito_millonario_2anios.csv"),
}

def clean_animal_name(name: str) -> str:
    if not isinstance(name, str):
        return ""
    name = name.strip()
    exact_map = {
        "AGUILA": "ÁGUILA", "ALACRAN": "ALACRÁN", "CAIMAN": "CAIMÁN",
        "CIEMPIES": "CIEMPIÉS", "DELFIN": "DELFÍN", "LEON": "LEÓN",
        "RATON": "RATÓN", "TIBURON": "TIBURÓN", "TUCAN": "TUCÁN",
        "BUFALO": "BÚFALO", "CHUGUIRE": "CHIGÜIRE", "PUERCOESPIN": "PUERCOESPÍN",
        "CAMALEON": "CAMALEÓN", "GAVILAN": "GAVILÁN", "HIPOPOTAMO": "HIPOPÓTAMO",
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

def fetch_url(url: str, session: requests.Session) -> Optional[str]:
    for attempt in range(3):
        try:
            resp = session.get(url, timeout=12)
            if resp.status_code == 200:
                return resp.text
            elif resp.status_code == 404:
                return None
        except Exception:
            time.sleep(0.3)
    return None

def download_missing_targets():
    targets = list(TARGETS_MAP.keys())
    session = requests.Session()
    session.headers.update(HEADERS)

    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=2 * 365 + 14)
    sundays = get_previous_sundays(start_date, today)

    records = {t: [] for t in targets}
    seen = {t: set() for t in targets}

    # Cargar datos previos si existen
    for t, path in TARGETS_MAP.items():
        if os.path.exists(path):
            try:
                prev_df = pd.read_csv(path)
                for _, r in prev_df.iterrows():
                    key = (str(r["fecha"]), str(r["hora"]))
                    if key not in seen[t]:
                        seen[t].add(key)
                        records[t].append(r.to_dict())
            except Exception:
                pass

    print(f"Descargando semanas de TuAzar para {targets}...")
    print(f"Total semanas a consultar: {len(sundays)}")

    # 1. Semana en curso
    html_semana = fetch_url(SEMANA_URL, session)
    if html_semana:
        data_sem = extract_targets_from_html(html_semana, targets)
        for t in targets:
            for d in data_sem[t]:
                k = (d["fecha"], d["hora"])
                if k not in seen[t]:
                    seen[t].add(k)
                    records[t].append(d)

    # 2. Descargar semanas anteriores concurrentemente
    def process_sunday(sunday_dt):
        url = ANTERIORES_URL.format(date=sunday_dt.strftime("%d-%m-%Y"))
        html = fetch_url(url, session)
        if not html:
            return {}
        return extract_targets_from_html(html, targets)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_date = {executor.submit(process_sunday, s): s for s in sundays}
        done_count = 0
        for f in concurrent.futures.as_completed(future_to_date):
            res_dict = f.result()
            done_count += 1
            if done_count % 20 == 0:
                print(f"  Progreso: {done_count}/{len(sundays)} semanas procesadas...")
            for t in targets:
                for d in res_dict.get(t, []):
                    k = (d["fecha"], d["hora"])
                    if k not in seen[t]:
                        seen[t].add(k)
                        records[t].append(d)

    print("\nGuardando resultados consolidados...")
    for t, fpath in TARGETS_MAP.items():
        recs = records[t]
        if not recs:
            print(f"[-] {t}: 0 registros encontrados.")
            continue
        df = pd.DataFrame(recs)
        df["dt_parsed"] = pd.to_datetime(df["fecha"] + " " + df["hora"], errors="coerce")
        df = df.sort_values(by="dt_parsed").drop(columns=["dt_parsed", "Unnamed: 0"], errors="ignore")
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        df.to_csv(fpath, index=False, encoding="utf-8")
        print(f"[+] {t}: {len(df)} sorteos guardados en {fpath} (Desde {df['fecha'].min()} hasta {df['fecha'].max()})")

if __name__ == "__main__":
    download_missing_targets()
