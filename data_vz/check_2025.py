import requests
import lxml.html

r = requests.get('https://www.tuazar.com/loteria/animalitos/resultados/anteriores/2025-01-12/', headers={'User-Agent': 'Mozilla/5.0'})
doc = lxml.html.fromstring(r.text)
cards = doc.xpath('//div[contains(@class, "lw-card")]')
print("Loterias presentes en Enero 2025:")
for c in cards:
    t = c.xpath('.//h3[contains(@class, "lw-title")]')
    if t:
        print(" -", t[0].text_content().strip())
