import requests
import re
import lxml.html

url = "https://lottobichos.com/sorteios/lottobrasil"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}
r = requests.get(url, headers=headers)
print("Status:", r.status_code)

tree = lxml.html.fromstring(r.text)
title = tree.xpath("//title/text()")
print("Title:", title)

# 1. Scripts
scripts = tree.xpath("//script")
print(f"Total scripts: {len(scripts)}")
for i, s in enumerate(scripts):
    src = s.get("src")
    text = s.text or ""
    if src:
        print(f"Script {i} src: {src}")
    elif text.strip():
        print(f"Script {i} inline (len {len(text)}): {text.strip()[:300]}")

# 2. Date inputs or links
inputs = tree.xpath("//input")
for inp in inputs:
    print("Input:", dict(inp.attrib))

links = tree.xpath("//a")
date_links = [l.get("href") for l in links if l.get("href") and any(k in l.get("href") for k in ["202", "sorteio", "data", "dia"])]
print(f"Total links with date/sorteio: {len(date_links)}")
for dl in set(date_links)[:20]:
    print("  Link:", dl)

# 3. Tables or result rows
tables = tree.xpath("//table")
print(f"Tables: {len(tables)}")
for i, t in enumerate(tables):
    rows = t.xpath(".//tr")
    print(f"  Table {i}: {len(rows)} rows")
    for r_idx, row in enumerate(rows[:5]):
        cols = [c.text_content().strip() for c in row.xpath(".//td|.//th")]
        print(f"    Row {r_idx}: {cols}")

# 4. Search for results in div / cards
divs_with_time = tree.xpath("//*[contains(@class, 'time') or contains(@class, 'hora') or contains(@class, 'sorteio') or contains(@class, 'resultado')]")
print(f"Divs with time/hora/sorteio/resultado: {len(divs_with_time)}")
for d in divs_with_time[:10]:
    print("  Tag:", d.tag, "Class:", d.get("class"), "Text:", d.text_content().strip()[:100])
