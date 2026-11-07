"""
Descargador específico para Lotto Activo RD Internacional desde TuAzar
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

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

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
    0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"
}

TARGET_NAME = "Lotto Activo RD Internacional"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "lotto_activo_rd_internacional.csv")

def clean_animal_name(name: str) -> str:
    if not isinstance(name, str):
        return ""
    name = name.strip()
    exact_map = {
        "AGUILA": "ÁGUILA", "ALACRAN": "ALACRÁN", "CAIMAN": "CAIMÁN", "CIEMPIES": "CIEMPIÉS",
        "DELFIN": "DELFÍN", "LEON": "LEÓN", "RATON": "RATÓN", "TIBURON": "TIBURÓN",
        "TUCAN": "TUCÁN", "BUFALO": "BÚFALO", "CHUGUIRE": "CHIGÜIRE", "PUERCOESPIN": "PUERCOESPÍN",
        "CAMALEON": "CAMALEÓN", "GAVILAN": "GAVILÁN", "HIPOPOTAMO": "HIPOPÓTAMO", "ARANA": "ARAÑA",
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

def extract_records_from_html(html_content: str) -> List[Dict]:
    results = []
    try:
        doc = lxml.html.fromstring(html_content)
    except Exception:
        return results

    cards = doc.xpath('//div[contains(@class, "lw-card")]')
    for card in cards:
        title_el = card.xpath('.//h3[contains(@class, "lw-title")]')
        if not title_el:
            continue
        card_title = title_el[0].text_content().strip()
        if TARGET_NAME.lower() not in card_title.lower():
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
                        results.append({
                            "fecha": dt.strftime("%Y-%m-%d"),
                            "dia": DIAS_MAP.get(dt.weekday(), ""),
                            "hora": draw_time,
                            "numero": str(numero),
                            "animal": str(animal),
                            "loteria": TARGET_NAME
                        })
    return results

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
            resp = session.get(url, timeout=15)
            if resp.status_code == 200:
                return resp.text
            elif resp.status_code == 404:
                return None
        except Exception:
            time.sleep(0.5)
    return None

def download_lotto_activo_rd(years: int = 2):
    session = requests.Session()
    session.headers.update(HEADERS)

    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=years * 365 + 14)
    sundays = get_previous_sundays(start_date, today)

    records = []
    seen = set()

    def add_records(rec_list):
        for r in rec_list:
            key = (r["fecha"], r["hora"])
            if key not in seen:
                seen.add(key)
                records.append(r)

    print("=" * 70)
    print(f"📥 DESCARGANDO HISTORIAL: {TARGET_NAME}")
    print(f"   Destino: {OUTPUT_FILE}")
    print(f"   Periodo: Últimos {years} años (~{len(sundays)} semanas)")
    print("=" * 70)

    # 1. Semana actual
    print("\n[+] Consultando semana actual...")
    html_curr = fetch_url(SEMANA_URL, session)
    if html_curr:
        add_records(extract_records_from_html(html_curr))
    print(f"    Registros semana actual: {len(records)}")

    # 2. Semanas históricas
    print(f"\n[+] Consultando {len(sundays)} semanas anteriores en paralelo...")
    urls_to_fetch = [(s, ANTERIORES_URL.format(date=s.strftime("%Y-%m-%d"))) for s in sundays]

    def worker(item):
        s_date, url = item
        s = requests.Session()
        s.headers.update(HEADERS)
        html = fetch_url(url, s)
        if html:
            return extract_records_from_html(html)
        return []

    completed = 0
    total_w = len(urls_to_fetch)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_item = {executor.submit(worker, item): item for item in urls_to_fetch}
        for future in concurrent.futures.as_completed(future_to_item):
            rec_extracted = future.result()
            add_records(rec_extracted)
            completed += 1
            if completed % 10 == 0 or completed == total_w:
                pct = (completed / total_w) * 100
                print(f"  [{completed:>3}/{total_w}] ({pct:5.1f}%) -> {len(records)} sorteos acumulados...", flush=True)

    if not records:
        print("[!] No se encontraron registros para", TARGET_NAME)
        return

    df = pd.DataFrame(records)
    df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
    df = df.sort_values(by="sort_dt").drop(columns=["sort_dt"]).reset_index(drop=True)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    min_f = df["fecha"].min()
    max_f = df["fecha"].max()
    print("\n" + "=" * 70)
    print(f"✓ DESCARGA EXITOSA: {len(df):,} sorteos descargados y guardados")
    print(f"  Archivo: {OUTPUT_FILE}")
    print(f"  Rango de Fechas: {min_f} a {max_f}")
    print(f"  Horarios registrados por día: {df['hora'].nunique()} ({', '.join(sorted(df['hora'].unique()))})")
    print("=" * 70)

if __name__ == "__main__":
    download_lotto_activo_rd(years=2)
