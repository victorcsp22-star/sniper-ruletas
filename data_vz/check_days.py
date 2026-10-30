import requests
import lxml.html

HEADERS = {"User-Agent": "Mozilla/5.0"}
r = requests.get('https://www.tuazar.com/loteria/animalitos/resultados/semana/', headers=HEADERS, timeout=12)
doc = lxml.html.fromstring(r.text)

for card in doc.xpath('//div[contains(@class, "lw-card")]'):
    title_el = card.xpath('.//h3[contains(@class, "lw-title")]')
    if title_el:
        title = title_el[0].text_content().strip()
        if title in ["Lotto Activo", "Lotto Activo RD Internacional", "La Granjita", "Ruleta Royal", "Guacharo Activo"]:
            print(f"=== {title} ===")
            table = card.xpath('.//table[contains(@class, "lw-table")]')[0]
            day_ths = table.xpath('.//thead//th[contains(@class, "lw-day")]')
            days = [th.xpath('.//span[contains(@class, "lw-day-num")]')[0].text_content().strip() for th in day_ths if th.xpath('.//span[contains(@class, "lw-day-num")]')]
            print("  Dias de la semana:", days)
            # Print row for 9:00 AM or 9:30 AM
            for row in table.xpath('.//tbody/tr'):
                h = row.xpath('.//th[contains(@class, "lw-time")]')[0].text_content().strip()
                if h in ["8:00 AM", "9:00 AM", "10:00 AM", "8:30 AM", "9:30 AM"]:
                    vals = []
                    for td in row.xpath('.//td'):
                        n = td.xpath('.//span[@class="lw-animal-num"]')
                        vals.append(n[0].text_content().strip() if n else "-")
                    print(f"  {h:>8} ->", " | ".join(vals))
