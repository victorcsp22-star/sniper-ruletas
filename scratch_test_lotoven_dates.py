import requests
import lxml.html
import re

url = "https://lotoven.com/animalitos-internacional"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def check_date(date_str):
    session = requests.Session()
    session.headers.update(headers)
    resp = session.post(url, data={"fecha": date_str}, timeout=15)
    doc = lxml.html.fromstring(resp.text)
    
    # Buscar resultados en el HTML
    text = " ".join(doc.text_content().split())
    # Buscar coincidencias como "17 Pavo", "08:00 AM", etc.
    draws = re.findall(r"(\d{1,2}|00)\s+([A-Za-zÁÉÍÓÚáéíóúñÑ]+)\s+Lotto Activo RDominicana\s+(\d{1,2}:\d{2}\s+[AP]M)", text)
    return len(draws), draws[:3]

print("Probando fechas en Lotoven:")
for d in ["2026-10-17", "2026-10-10", "2026-09-01", "2026-08-01", "2026-05-01", "2026-01-01", "2025-06-01", "2024-06-01"]:
    n, sample = check_date(d)
    print(f"Fecha {d}: {n} sorteos encontrados. Muestra: {sample}")
