import requests
import lxml.html

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

r = requests.get('https://www.tuazar.com/loteria/animalitos/resultados/semana/', headers=HEADERS, timeout=15)
doc = lxml.html.fromstring(r.text)
cards = doc.xpath('//div[contains(@class, "lw-card")]')

print("TOTAL CARDS:", len(cards))
for i, c in enumerate(cards):
    t = c.xpath('.//h3[contains(@class, "lw-title")]')
    if t:
        title = t[0].text_content().strip()
        times = [x.text_content().strip() for x in c.xpath('.//table//tbody/tr/th')]
        print(f"[{i:2d}] Title: '{title}' | Horas: {times[:3]}... ({len(times)} sorteos/día)")
