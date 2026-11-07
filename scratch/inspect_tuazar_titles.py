import requests, lxml.html

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
r_sem = requests.get('https://www.tuazar.com/loteria/animalitos/resultados/semana/', headers=headers, timeout=15)
doc_sem = lxml.html.fromstring(r_sem.text)
titles = doc_sem.xpath('//h3/text()')
print("Titulos encontrados en TuAzar /semana/:")
for t in sorted(set(x.strip() for x in titles if x.strip())):
    print("  *", t)
