import requests
import lxml.html

r = requests.get('https://www.tuazar.com/loteria/animalitos/resultados/anteriores/2025-01-12/', headers={'User-Agent': 'Mozilla/5.0'})
doc = lxml.html.fromstring(r.text)
for c in doc.xpath('//div[contains(@class, "lw-card")]'):
    t = c.xpath('.//h3[contains(@class, "lw-title")]')
    if t:
        title = t[0].text_content().strip()
        cells = [x.text_content().strip() for x in c.xpath('.//table//tbody/tr[1]/td')]
        non_empty = [x for x in cells if x != '-']
        print(f'{title:35s}: {len(non_empty)}/7 dias con datos')
