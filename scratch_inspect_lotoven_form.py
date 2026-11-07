import requests
import lxml.html

url = "https://lotoven.com/animalitos-internacional"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}
resp = requests.get(url, headers=headers, timeout=15)
doc = lxml.html.fromstring(resp.text)

forms = doc.xpath("//form")
print(f"Total forms: {len(forms)}")
for f in forms:
    print("Action:", f.get("action"))
    print("Method:", f.get("method"))
    for inp in f.xpath(".//input | .//select | .//button"):
        print("  Input:", inp.tag, inp.get("name"), inp.get("type"), inp.get("value"))

# Ver los sorteos de hoy mostrados en la página
draw_cards = doc.xpath("//div[contains(@class, 'single-item')] | //div[contains(@class, 'lottery')] | //div[contains(@class, 'card')]")
print(f"\nDraw cards: {len(draw_cards)}")

for dc in doc.xpath("//div[contains(@class, 'lottery-item') or contains(@class, 'single') or contains(@class, 'card-body') or contains(@class, 'result')]")[:15]:
    txt = " ".join(dc.text_content().split())
    if any(h in txt for h in ["AM", "PM"]):
        print("Card:", txt)
