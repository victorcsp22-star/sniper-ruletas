import requests
import re
import lxml.html

url = "https://lottobichos.com/sorteios/lottobrasil"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}
r = requests.get(url, headers=headers)
tree = lxml.html.fromstring(r.text)

scripts = tree.xpath("//script")
print("=== SCRIPT 1 (window.GB) ===")
print(scripts[1].text)

print("\n=== TABLES ===")
tables = tree.xpath("//table")
for i, t in enumerate(tables):
    print(f"Table {i} class: {t.get('class')}, id: {t.get('id')}")
    rows = t.xpath(".//tr")
    print(f"  Rows count: {len(rows)}")
    for row in rows[:8]:
        cells = [c.text_content().strip().replace('\n', ' ') for c in row.xpath(".//td|.//th")]
        print("   ", cells)

print("\n=== CARDS / CONTAINERS ===")
for div in tree.xpath("//div[contains(@class, 'result') or contains(@class, 'sorteio') or contains(@class, 'container')]")[:10]:
    print("Div class:", div.get("class"), "id:", div.get("id"))
