import datetime
import os
import sys
import time
from typing import List, Dict, Optional
import lxml.html
import pandas as pd
import requests

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

def parse_date_dmy(dmy_str: str) -> Optional[datetime.date]:
    try:
        parts = dmy_str.strip().split('/')
        if len(parts) == 3:
            return datetime.date(int(parts[2]), int(parts[1]), int(parts[0]))
    except Exception:
        pass
    return None

def extract_all_targets_from_html(html_content: str, target_lotteries: List[str]) -> Dict[str, List[Dict]]:
    res = {t: [] for t in target_lotteries}
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
        for t in target_lotteries:
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
                    animal = animal_el[0].text_content().strip()
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

def scrape_multi(targets: List[str], years: int = 2):
    session = requests.Session()
    session.headers.update(HEADERS)

    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=years * 365 + 14)
    sundays = get_previous_sundays(start_date, today)

    records = {t: [] for t in targets}
    seen = {t: set() for t in targets}

    def add_to_target(t, rec_list):
        for r in rec_list:
            key = (r["fecha"], r["hora"])
            if key not in seen[t]:
                seen[t].add(key)
                records[t].append(r)

    print(f"Descargando {years} años para: {', '.join(targets)}")
    print(f"Total semanas a consultar: {len(sundays)}")

    # Semana actual
    try:
        r_curr = session.get(SEMANA_URL, timeout=12)
        if r_curr.status_code == 200:
            extracted = extract_all_targets_from_html(r_curr.text, targets)
            for t in targets:
                add_to_target(t, extracted[t])
    except Exception as e:
        print(f"Error semana actual: {e}")

    # Semanas anteriores
    total_w = len(sundays)
    for idx, sunday in enumerate(sundays, 1):
        sunday_str = sunday.strftime("%Y-%m-%d")
        url = ANTERIORES_URL.format(date=sunday_str)
        
        for attempt in range(2):
            try:
                resp = session.get(url, timeout=12)
                if resp.status_code == 200:
                    extracted = extract_all_targets_from_html(resp.text, targets)
                    for t in targets:
                        add_to_target(t, extracted[t])
                    break
                elif resp.status_code == 404:
                    break
            except Exception:
                time.sleep(0.5)

        pct = (idx / total_w) * 100
        status_counts = " | ".join([f"{t}: {len(records[t])}" for t in targets])
        print(f"\r[{idx}/{total_w}] ({pct:5.1f}%) | {status_counts}", end="", flush=True)
        time.sleep(0.15)

    print("\nDescarga completa. Guardando CSVs...")
    
    file_names = {
        "La Granjita": "la_granjita_2anios.csv",
        "Ruleta Royal": "ruleta_royal_2anios.csv",
        "Guacharo Activo": "guacharo_activo_2anios.csv"
    }

    for t in targets:
        rec_list = records[t]
        if not rec_list:
            print(f"[!] Sin registros para {t}")
            continue
        df = pd.DataFrame(rec_list)
        try:
            df["_h"] = pd.to_datetime(df["hora"], format="%I:%M %p", errors="coerce").dt.time
            df = df.sort_values(by=["fecha", "_h"]).drop(columns=["_h"])
        except Exception:
            df = df.sort_values(by=["fecha", "hora"])
        
        fname = file_names.get(t, f"{t.lower().replace(' ', '_')}.csv")
        df.to_csv(fname, index=False, encoding="utf-8-sig")
        print(f" -> Guardado {fname}: {len(df):,} sorteos ({df['fecha'].min()} a {df['fecha'].max()})")

if __name__ == "__main__":
    targets = ["La Granjita", "Ruleta Royal", "Guacharo Activo"]
    scrape_multi(targets, years=2)
