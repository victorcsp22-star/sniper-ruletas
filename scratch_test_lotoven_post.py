import requests
import lxml.html

url = "https://lotoven.com/animalitos-internacional"
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://lotoven.com/animalitos-internacional",
    "Origin": "https://lotoven.com"
})

r1 = session.get(url)
print("GET Cookies:", session.cookies.get_dict())

r2 = session.post(url, data={"fecha": "2026-10-15"})
print("POST Status:", r2.status_code)
doc = lxml.html.fromstring(r2.text)
inp = doc.xpath('//input[@name="fecha"]')
if inp:
    print("Input value returned in HTML:", inp[0].get("value"))

cards = doc.xpath('//div[contains(@class, "card")]')
print(f"Cards found: {len(cards)}")
for c in cards:
    txt = " ".join(c.text_content().split())
    if "2026" in txt or "Lotto" in txt:
        print("Card text:", txt[:200])
