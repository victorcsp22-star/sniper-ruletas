import requests
import lxml.html

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

r = requests.get('https://www.tuazar.com/loteria/animalitos/resultados/semana/', headers=HEADERS, timeout=15)
doc = lxml.html.fromstring(r.text)
cards = doc.xpath('//div[contains(@class, "lw-card")]')
titles = []
for c in cards:
    t = c.xpath('.//h3[contains(@class, "lw-title")]')
    if t:
        titles.append(t[0].text_content().strip())
print('Found Lotteries:', titles)
