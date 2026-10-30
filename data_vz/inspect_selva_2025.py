import requests
import lxml.html

r = requests.get('https://www.tuazar.com/loteria/animalitos/resultados/anteriores/2025-01-12/', headers={'User-Agent': 'Mozilla/5.0'})
doc = lxml.html.fromstring(r.text)
for c in doc.xpath('//div[contains(@class, "lw-card")]'):
    t = c.xpath('.//h3[contains(@class, "lw-title")]')
    if t and 'Selva' in t[0].text_content():
        print('Selva card title:', repr(t[0].text_content().strip()))
        table = c.xpath('.//table')
        print('Table found:', len(table))
        if table:
            rows = table[0].xpath('.//tbody/tr')
            print('Num rows:', len(rows))
            for row in rows[:5]:
                cells = [x.text_content().strip().replace('\n', ' ') for x in row.xpath('.//th | .//td')]
                print('Row:', cells)
