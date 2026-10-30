"""
Bot Scraper para Resultados Históricos de Loterías de Animalitos (TuAzar)
Permite extraer el historial completo (ej. 2 años o más) de Lotto Activo,
La Granjita, Ruleta Royal, Guacharo Activo y exportarlo a CSV listo para Excel y análisis.
"""

import argparse
import datetime
import os
import sys
import time
from typing import List, Dict, Optional, Tuple

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

# Normalización de días
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
    """Convierte string DD/MM/YYYY a objeto date."""
    try:
        parts = dmy_str.strip().split('/')
        if len(parts) == 3:
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            return datetime.date(year, month, day)
    except Exception:
        pass
    return None


def extract_lottery_from_html(html_content: str, target_lottery: str = "Lotto Activo") -> List[Dict]:
    """
    Parsea una página HTML de TuAzar y extrae todos los sorteos para la lotería objetivo.
    Retorna una lista de diccionarios con los campos:
    [fecha, dia, hora, numero, animal, loteria]
    """
    records = []
    doc = lxml.html.fromstring(html_content)
    cards = doc.xpath('//div[contains(@class, "lw-card")]')

    target_card = None
    for card in cards:
        title_el = card.xpath('.//h3[contains(@class, "lw-title")]')
        if title_el:
            card_title = title_el[0].text_content().strip()
            if target_lottery.lower() in card_title.lower():
                target_card = card
                break

    if target_card is None:
        return records

    table = target_card.xpath('.//table[contains(@class, "lw-table")]')
    if not table:
        return records

    table = table[0]

    # Extraer encabezados de días (columnas)
    day_headers = table.xpath('.//thead//th[contains(@class, "lw-day")]')
    column_dates: List[Optional[datetime.date]] = []

    for th in day_headers:
        day_num_el = th.xpath('.//span[contains(@class, "lw-day-num")]')
        if day_num_el:
            d = parse_date_dmy(day_num_el[0].text_content())
            column_dates.append(d)
        else:
            column_dates.append(None)

    # Extraer filas (horarios de sorteo)
    rows = table.xpath('.//tbody/tr')
    for row in rows:
        time_el = row.xpath('.//th[contains(@class, "lw-time")]')
        draw_time = time_el[0].text_content().strip() if time_el else ""

        cells = row.xpath('.//td')
        for dt, cell in zip(column_dates, cells):
            if dt is None:
                continue

            # Buscar número y nombre del animalito
            num_el = cell.xpath('.//span[@class="lw-animal-num"]')
            animal_el = cell.xpath('.//span[@class="lw-animal"]')

            if num_el and animal_el:
                numero = num_el[0].text_content().strip()
                animal = animal_el[0].text_content().strip()
                
                # Descartar celdas vacías o marcadores sin sorteo
                if numero and animal and numero != "-":
                    records.append({
                        "fecha": dt.strftime("%Y-%m-%d"),
                        "dia": DIAS_MAP.get(dt.weekday(), ""),
                        "hora": draw_time,
                        "numero": numero,
                        "animal": animal,
                        "loteria": target_lottery
                    })

    return records


def get_previous_sundays(start_date: datetime.date, end_date: datetime.date) -> List[datetime.date]:
    """Genera lista de domingos entre start_date y end_date hacia atrás."""
    # Encontrar el domingo anterior o igual a end_date
    current = end_date
    while current.weekday() != 6:  # 6 es domingo
        current -= datetime.timedelta(days=1)

    sundays = []
    while current >= start_date:
        sundays.append(current)
        current -= datetime.timedelta(days=7)

    return sundays


def scrape_lottery_history(
    target_lottery: str = "Lotto Activo",
    years: int = 2,
    output_csv: str = "lotto_activo_historial.csv",
    delay: float = 0.35,
    max_retries: int = 3
) -> pd.DataFrame:
    """
    Descarga y compila el historial de la lotería especificada.
    """
    session = requests.Session()
    session.headers.update(HEADERS)

    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=years * 365 + 14)  # margen extra
    sundays = get_previous_sundays(start_date, today)

    print(f"==================================================")
    print(f" Bot de Lotería: {target_lottery}")
    print(f" Rango de búsqueda: {years} año(s) (~{len(sundays)} semanas)")
    print(f" Desde: {start_date}  Hasta: {today}")
    print(f" Archivo de salida: {output_csv}")
    print(f"==================================================\n")

    all_records: List[Dict] = []
    seen_keys = set()

    def add_records(recs: List[Dict]):
        added = 0
        for r in recs:
            key = (r["fecha"], r["hora"], r["loteria"])
            if key not in seen_keys:
                seen_keys.add(key)
                all_records.append(r)
                added += 1
        return added

    # 1. Obtener semana en curso
    print("1/2) Consultando la semana actual...")
    try:
        r_curr = session.get(SEMANA_URL, timeout=12)
        if r_curr.status_code == 200:
            cur_recs = extract_lottery_from_html(r_curr.text, target_lottery)
            added = add_records(cur_recs)
            print(f"   -> Semana en curso: {added} sorteos obtenidos.")
    except Exception as e:
        print(f"   [!] Advertencia al obtener semana actual: {e}")

    # 2. Iterar semanas anteriores
    total_weeks = len(sundays)
    print(f"\n2/2) Descargando {total_weeks} semanas anteriores...")

    for idx, sunday in enumerate(sundays, 1):
        sunday_str = sunday.strftime("%Y-%m-%d")
        url = ANTERIORES_URL.format(date=sunday_str)

        success = False
        for attempt in range(1, max_retries + 1):
            try:
                resp = session.get(url, timeout=12)
                if resp.status_code == 200:
                    recs = extract_lottery_from_html(resp.text, target_lottery)
                    added = add_records(recs)
                    success = True
                    break
                elif resp.status_code == 404:
                    # Semana no disponible
                    break
                else:
                    time.sleep(1.0)
            except Exception:
                time.sleep(1.0 * attempt)

        # Barra de progreso sencilla en consola
        pct = (idx / total_weeks) * 100
        print(f"\rProgreso: [{idx}/{total_weeks}] ({pct:5.1f}%) | Semana: {sunday_str} | Total sorteos: {len(all_records)}", end="", flush=True)

        if delay > 0:
            time.sleep(delay)

    print("\n\nDescarga finalizada.")

    if not all_records:
        print("[!] No se encontraron resultados. Verifica la conexión o el nombre de la lotería.")
        return pd.DataFrame()

    df = pd.DataFrame(all_records)

    # Ordenar cronológicamente (Fecha ascendente, Hora)
    # Para ordenar horas adecuadamente:
    try:
        df["_hora_dt"] = pd.to_datetime(df["hora"], format="%I:%M %p", errors="coerce").dt.time
        df = df.sort_values(by=["fecha", "_hora_dt"]).drop(columns=["_hora_dt"])
    except Exception:
        df = df.sort_values(by=["fecha", "hora"])

    # Guardar en CSV con codificación utf-8-sig (compatible directamente con Microsoft Excel en español)
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"[OK] Archivo guardado con éxito:")
    print(f"     -> {os.path.abspath(output_csv)}")
    print(f"     -> Total de sorteos guardados: {len(df)}")
    print(f"     -> Período cubierto: {df['fecha'].min()} al {df['fecha'].max()}\n")

    return df


def main():
    parser = argparse.ArgumentParser(description="Bot de extracción de resultados históricos de lotería.")
    parser.add_argument("--loteria", type=str, default="Lotto Activo", help="Nombre de la lotería (ej. 'Lotto Activo', 'La Granjita', etc.)")
    parser.add_argument("--years", type=int, default=2, help="Cantidad de años hacia atrás a descargar (por defecto: 2)")
    parser.add_argument("--output", type=str, default="lotto_activo_2anios.csv", help="Nombre o ruta del archivo CSV de salida")
    parser.add_argument("--delay", type=float, default=0.25, help="Pausa entre peticiones en segundos (por defecto: 0.25)")

    args = parser.parse_args()
    scrape_lottery_history(
        target_lottery=args.loteria,
        years=args.years,
        output_csv=args.output,
        delay=args.delay
    )


if __name__ == "__main__":
    main()
