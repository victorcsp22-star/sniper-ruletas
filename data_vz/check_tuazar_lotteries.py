import sys
import requests
import lxml.html

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

url = 'https://www.tuazar.com/loteria/animalitos/resultados/semana/'
headers = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
}
r = requests.get(url, headers=headers, timeout=15)
print("Status:", r.status_code, "Length:", len(r.content))

doc = lxml.html.fromstring(r.content)
cards = doc.xpath('//div[contains(@class, "lw-card")]')
print(f"Total lw-card encontradas: {len(cards)}")

titles = []
for c in cards:
    t = c.xpath('.//h3[contains(@class, "lw-title")]')
    if t:
        titles.append(t[0].text_content().strip())

print(f"Total títulos encontrados: {len(titles)}")
for idx, title in enumerate(titles):
    print(f"{idx+1}. {title}")
