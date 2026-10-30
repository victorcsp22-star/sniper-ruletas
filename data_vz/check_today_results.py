import requests
import lxml.html
import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
r = requests.get('https://www.tuazar.com/loteria/animalitos/resultados/semana/', headers=HEADERS, timeout=12)
doc = lxml.html.fromstring(r.text)

for card in doc.xpath('//div[contains(@class, "lw-card")]'):
    title_el = card.xpath('.//h3[contains(@class, "lw-title")]')
    if title_el:
        title = title_el[0].text_content().strip()
        if title in ["Lotto Activo", "Lotto Activo RD Internacional", "La Granjita", "Ruleta Royal", "Guacharo Activo"]:
            print(f"=== {title} ===")
            table = card.xpath('.//table[contains(@class, "lw-table")]')
            if table:
                rows = table[0].xpath('.//tbody/tr')
                for row in rows[:4]: # first few hours
                    th = row.xpath('.//th[contains(@class, "lw-time")]')
                    h = th[0].text_content().strip() if th else ""
                    # last td
                    tds = row.xpath('.//td')
                    if tds:
                        last_td = tds[-1]
                        n = last_td.xpath('.//span[@class="lw-animal-num"]')
                        a = last_td.xpath('.//span[@class="lw-animal"]')
                        num = n[0].text_content().strip() if n else "-"
                        anim = a[0].text_content().strip() if a else "-"
                        print(f"  {h:>8} -> {num} ({anim})")
