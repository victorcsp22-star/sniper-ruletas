"""
========================================================================================
 DESCARGADOR DE DATOS HISTÓRICOS (TUAZAR) - NUEVAS RULETAS
========================================================================================
Descarga el historial de 2 años (2024-2026) para las siguientes ruletas solicitadas:
 1. Monje Millonario
 2. Lotto Gato
 3. Gatazo
 4. Granja Millonaria (Animalitos y Granjazo)
 5. Mega Animal 40
 6. Loto Chaima

Guarda los archivos CSV limpios y ordenados en C:\\Users\\victo\\nuevas_ruletas\\
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
    0: "Lunes",
    1: "Martes",
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo"
}

TARGETS_MAP = {
    "Monje Millonario": "monje_millonario.csv",
    "Lotto Gato": "lotto_gato.csv",
    "Gatazo": "gatazo.csv",
    "Granja Millonaria - Animalitos": "granja_millonaria_animalitos.csv",
    "Granja Millonaria - Granjazo": "granja_millonaria_granjazo.csv",
    "Mega Animal 40": "mega_animal_40.csv",
    "Loto Chaima": "loto_chaima.csv"
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

def download_all(years: int = 2):
    targets = list(TARGETS_MAP.keys())
    session = requests.Session()
    session.headers.update(HEADERS)

    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=years * 365 + 14)
    sundays = get_previous_sundays(start_date, today)

    records = {t: [] for t in targets}
    seen = {t: set() for t in targets}

    def add_records(extracted_dict):
        for t, rec_list in extracted_dict.items():
            for r in rec_list:
                key = (r["fecha"], r["hora"])
                if key not in seen[t]:
                    seen[t].add(key)
                    records[t].append(r)

    print("=" * 80)
    print(f" 📥 DESCARGA DE HISTORIAL TUAZAR (ÚLTIMOS {years} AÑOS)")
    print(f"    Destino: {OUTPUT_DIR}")
    print(f"    Ruletas objetivo ({len(targets)}): {', '.join(targets)}")
    print(f"    Total semanas a consultar: {len(sundays)}")
    print("=" * 80)

    # 1. Semana actual
    print("\n[+] Descargando semana en curso...")
    html_curr = fetch_url(SEMANA_URL, session)
    if html_curr:
        add_records(extract_targets_from_html(html_curr, targets))

    # 2. Semanas anteriores en paralelo (hilos concurrentes)
    print(f"\n[+] Descargando semanas históricas ({len(sundays)} semanas)...")
    urls_to_fetch = [(s, ANTERIORES_URL.format(date=s.strftime("%Y-%m-%d"))) for s in sundays]

    def worker(item):
        s_date, url = item
        s = requests.Session()
        s.headers.update(HEADERS)
        html = fetch_url(url, s)
        if html:
            return extract_targets_from_html(html, targets)
        return {t: [] for t in targets}

    completed = 0
    total_w = len(urls_to_fetch)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_item = {executor.submit(worker, item): item for item in urls_to_fetch}
        for future in concurrent.futures.as_completed(future_to_item):
            res_extracted = future.result()
            add_records(res_extracted)
            completed += 1
            if completed % 10 == 0 or completed == total_w:
                pct = (completed / total_w) * 100
                counts_str = " | ".join([f"{t.split('-')[0].strip()}: {len(records[t])}" for t in targets[:3]])
                print(f"  [{completed:>3}/{total_w}] ({pct:5.1f}%) -> {counts_str}...", flush=True)

    print("\n" + "=" * 80)
    print(" 💾 PROCESANDO Y GUARDANDO ARCHIVOS CSV")
    print("=" * 80)

    summary_rows = []
    for t in targets:
        rec_list = records[t]
        fname = TARGETS_MAP[t]
        fpath = os.path.join(OUTPUT_DIR, fname)
        if not rec_list:
            print(f"[!] Sin registros para {t}")
            continue

        df = pd.DataFrame(rec_list)
        df["_h"] = pd.to_datetime(df["hora"], format="%I:%M %p", errors="coerce").dt.time
        df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        df = df.sort_values(by="sort_dt").drop(columns=["_h", "sort_dt"]).reset_index(drop=True)
        df.to_csv(fpath, index=False, encoding="utf-8-sig")

        min_f = df["fecha"].min()
        max_f = df["fecha"].max()
        tot = len(df)
        print(f" [✓] {t:<30} -> {fname:<32} | {tot:>6,} sorteos ({min_f} a {max_f})")
        summary_rows.append({
            "Ruleta": t,
            "Archivo": fname,
            "Total Sorteos": tot,
            "Fecha Inicio": min_f,
            "Fecha Fin": max_f
        })

    df_sum = pd.DataFrame(summary_rows)
    df_sum.to_csv(os.path.join(OUTPUT_DIR, "resumen_descarga.csv"), index=False, encoding="utf-8-sig")
    print("\n[✓] Descarga completa y exitosa de todas las ruletas en:")
    print(f"    {OUTPUT_DIR}\n")

if __name__ == "__main__":
    download_all(years=2)
