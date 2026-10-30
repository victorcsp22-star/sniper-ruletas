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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

DIAS_MAP = {
    0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves",
    4: "Viernes", 5: "Sábado", 6: "Domingo"
}

def parse_date_dmy(dmy_str: str) -> Optional[datetime.date]:
    try:
        parts = dmy_str.strip().split('/')
        if len(parts) == 3:
            return datetime.date(int(parts[2]), int(parts[1]), int(parts[0]))
    except Exception:
        pass
    return None

TARGETS = ["Selva Plus", "El Guacharito Millonario", "Lotto Activo RD Internacional"]

def extract_from_html(html_content: str) -> Dict[str, List[Dict]]:
    res = {t: [] for t in TARGETS}
    try:
        doc = lxml.html.fromstring(html_content)
    except Exception:
        return res

    for card in doc.xpath('//div[contains(@class, "lw-card")]'):
        t_el = card.xpath('.//h3[contains(@class, "lw-title")]')
        if not t_el:
            continue
        title = t_el[0].text_content().strip()
        
        target = None
        for t in TARGETS:
            if title == t:
                target = t
                break
        if not target:
            continue

        table = card.xpath('.//table[contains(@class, "lw-table")]')
        if not table:
            continue
        table = table[0]

        day_headers = table.xpath('.//thead//th[contains(@class, "lw-day")]')
        dates = []
        for th in day_headers:
            d_el = th.xpath('.//span[contains(@class, "lw-day-num")]')
            if d_el:
                dates.append(parse_date_dmy(d_el[0].text_content()))
            else:
                dates.append(None)

        for row in table.xpath('.//tbody/tr'):
            time_el = row.xpath('.//th[contains(@class, "lw-time")]')
            draw_time = time_el[0].text_content().strip() if time_el else ""

            for dt, cell in zip(dates, row.xpath('.//td')):
                if dt is None:
                    continue
                num_el = cell.xpath('.//span[@class="lw-animal-num"]')
                anim_el = cell.xpath('.//span[@class="lw-animal"]')
                if num_el and anim_el:
                    num = num_el[0].text_content().strip()
                    anim = anim_el[0].text_content().strip()
                    if num and anim and num != "-":
                        res[target].append({
                            "fecha": dt.strftime("%Y-%m-%d"),
                            "dia": DIAS_MAP.get(dt.weekday(), ""),
                            "hora": draw_time,
                            "numero": str(num),
                            "animal": str(anim),
                            "loteria": target
                        })
    return res

def get_sundays(start_date: datetime.date, end_date: datetime.date) -> List[datetime.date]:
    curr = end_date
    while curr.weekday() != 6:
        curr -= datetime.timedelta(days=1)
    sundays = []
    while curr >= start_date:
        sundays.append(curr)
        curr -= datetime.timedelta(days=7)
    return sundays

def scrape_extra():
    session = requests.Session()
    session.headers.update(HEADERS)
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=2 * 365 + 14)
    sundays = get_sundays(start_date, today)

    records = {t: [] for t in TARGETS}
    seen = {t: set() for t in TARGETS}

    def add(t, recs):
        for r in recs:
            k = (r["fecha"], r["hora"])
            if k not in seen[t]:
                seen[t].add(k)
                records[t].append(r)

    print("Consultando semana actual...")
    try:
        r = session.get(SEMANA_URL, timeout=12)
        if r.status_code == 200:
            ext = extract_from_html(r.text)
            for t in TARGETS:
                add(t, ext[t])
    except Exception as e:
        print(f"Error semana: {e}")

    total_w = len(sundays)
    print(f"Descargando {total_w} semanas...")
    for idx, sunday in enumerate(sundays, 1):
        sunday_str = sunday.strftime("%Y-%m-%d")
        url = ANTERIORES_URL.format(date=sunday_str)
        try:
            resp = session.get(url, timeout=12)
            if resp.status_code == 200:
                ext = extract_from_html(resp.text)
                for t in TARGETS:
                    add(t, ext[t])
        except Exception:
            pass

        pct = (idx / total_w) * 100
        status_c = " | ".join([f"{t}: {len(records[t])}" for t in TARGETS])
        print(f"\r[{idx}/{total_w}] ({pct:5.1f}%) | {status_c}", end="", flush=True)
        time.sleep(0.12)

    print("\nGuardando CSVs...")
    files_map = {
        "Selva Plus": "selva_plus_2anios.csv",
        "El Guacharito Millonario": "guacharito_millonario_2anios.csv",
        "Lotto Activo RD Internacional": "lotto_activo_rd_2anios.csv"
    }

    for t in TARGETS:
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
        fname = files_map[t]
        df.to_csv(fname, index=False, encoding="utf-8-sig")
        print(f" -> Guardado {fname}: {len(df):,} sorteos ({df['fecha'].min()} a {df['fecha'].max()})")

if __name__ == "__main__":
    scrape_extra()
