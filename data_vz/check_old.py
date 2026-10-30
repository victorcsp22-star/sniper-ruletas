import requests
import lxml.html

HEADERS = {"User-Agent": "Mozilla/5.0"}
for yr in ['2024-01-14', '2023-01-15', '2022-01-16']:
    url = f'https://www.tuazar.com/loteria/animalitos/resultados/anteriores/{yr}/'
    r = requests.get(url, headers=HEADERS, timeout=12)
    doc = lxml.html.fromstring(r.text)
    cards = doc.xpath('//div[contains(@class, "lw-card")]')
    titles = [c.xpath('.//h3[contains(@class, "lw-title")]')[0].text_content().strip() for c in cards if c.xpath('.//h3[contains(@class, "lw-title")]')]
    print(f"Año {yr[:4]}:", [t for t in titles if 'ruleta' in t.lower() or 'activa' in t.lower()])
