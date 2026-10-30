import requests
import lxml.html

r = requests.get('https://www.tuazar.com/loteria/animalitos/resultados/semana/', headers={'User-Agent': 'Mozilla/5.0'}, timeout=12)
doc = lxml.html.fromstring(r.text)
cards = doc.xpath('//div[contains(@class, "lw-card")]')
main_5 = ['Lotto Activo', 'La Granjita', 'Ruleta Royal', 'Guacharo Activo', 'Selva Plus']

print("--- Loterias disponibles en TuAzar (Excluyendo las 5 del Portafolio) ---")
for c in cards:
    t = c.xpath('.//h3[contains(@class, "lw-title")]')
    if t:
        title = t[0].text_content().strip()
        if title not in main_5:
            tds = c.xpath('.//table//tbody//td')
            nums = []
            for td in tds:
                txt = td.text_content().strip()
                if txt and txt != '-':
                    nums.append(txt)
            print(f"{title:35s}: {len(nums):3d} sorteos activos esta semana")
