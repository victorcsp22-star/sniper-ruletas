import requests
import lxml.html

HEADERS = {"User-Agent": "Mozilla/5.0"}
r = requests.get('https://www.tuazar.com/loteria/animalitos/resultados/semana/', headers=HEADERS, timeout=12)
doc = lxml.html.fromstring(r.text)

for c in doc.xpath('//div[contains(@class, "lw-card")]'):
    t = c.xpath('.//h3[contains(@class, "lw-title")]')
    if t and t[0].text_content().strip() == "Selva Plus":
        print("Encontrada Selva Plus:")
        table = c.xpath('.//table[contains(@class, "lw-table")]')[0]
        rows = table.xpath('.//tbody/tr')
        times = [r.xpath('.//th[contains(@class, "lw-time")]')[0].text_content().strip() for r in rows]
        print("Horarios Selva Plus:", times)
