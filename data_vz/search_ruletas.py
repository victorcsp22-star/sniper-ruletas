import requests
import lxml.html

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# 1. Check week page for Ruleta Activa and Selva Plus
r = requests.get('https://www.tuazar.com/loteria/animalitos/resultados/semana/', headers=HEADERS, timeout=12)
doc = lxml.html.fromstring(r.text)
cards = doc.xpath('//div[contains(@class, "lw-card")]')

print("Buscando en la semana actual:")
for c in cards:
    t = c.xpath('.//h3[contains(@class, "lw-title")]')
    if t:
        title = t[0].text_content().strip()
        if any(x.lower() in title.lower() for x in ["ruleta", "selva", "activa"]):
            print(f" -> Encontrada: '{title}'")

# 2. Check an older historical page from 2024 to see if Ruleta Activa existed then
r_old = requests.get('https://www.tuazar.com/loteria/animalitos/resultados/anteriores/2024-10-13/', headers=HEADERS, timeout=12)
doc_old = lxml.html.fromstring(r_old.text)
cards_old = doc_old.xpath('//div[contains(@class, "lw-card")]')

print("\nBuscando en página histórica de 2024:")
for c in cards_old:
    t = c.xpath('.//h3[contains(@class, "lw-title")]')
    if t:
        title = t[0].text_content().strip()
        if any(x.lower() in title.lower() for x in ["ruleta", "selva", "activa"]):
            print(f" -> Encontrada en 2024: '{title}'")
