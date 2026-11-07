import requests
import lxml.html
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def test_date(date_str):
    url = f"https://lotoven.com/animalitos-internacional/{date_str}"
    resp = requests.get(url, headers=headers, timeout=12)
    if resp.status_code != 200:
        return resp.status_code, 0, []
    
    doc = lxml.html.fromstring(resp.text)
    txt = " ".join(doc.text_content().split())
    # Extraer sorteos
    # Patrón: numero animal loteria hora
    draws = re.findall(r"(\d{1,2}|00)\s+([A-Za-zÁÉÍÓÚáéíóúñÑ]+)\s+(Lotto Activo [A-Za-z\s]+)\s+(\d{1,2}:\d{2}\s+[AP]M)", txt)
    return resp.status_code, len(draws), draws[:2]

test_dates = [
    "2026-10-16",
    "2026-10-10",
    "2026-09-15",
    "2026-09-01",
    "2026-08-15",
    "2026-08-01",
    "2026-07-01",
    "2026-06-01",
    "2026-05-01",
    "2026-04-01",
    "2026-03-01",
    "2026-02-01",
    "2026-01-01",
    "2025-10-01",
    "2025-06-01",
    "2024-10-01",
    "2024-01-01"
]

print("=== SONDEO DE PROFUNDIDAD HISTÓRICA EN LOTOVEN ===")
for d in test_dates:
    status, count, sample = test_date(d)
    print(f"Fecha {d} | Status: {status} | Sorteos: {count:>2} | Muestra: {sample}")
