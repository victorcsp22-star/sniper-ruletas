import urllib.request
import re

url = "https://www.tuazar.com/loteria/animalitos/resultados/"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=10) as r:
    html = r.read().decode("utf-8", errors="ignore")

cards = re.findall(r'<div class="[^"]*lc-card[^"]*">(.*?)</div>\s*<!--\s*/\.lc-card\s*-->', html, re.DOTALL)
print(f"Cards found with comment: {len(cards)}")
if not cards:
    # Try split by lc-card
    cards = re.split(r'<div class="[^"]*lc-card[^"]*"', html)[1:]
    print(f"Cards found with split: {len(cards)}")

for i, c in enumerate(cards):
    m_title = re.search(r'<h3 class="lc-title"[^>]*>(.*?)</h3>', c, re.DOTALL)
    if m_title:
        title = re.sub(r'<[^>]+>', '', m_title.group(1)).strip()
        tiles = re.findall(r'lc-tile-num[^>]*>(.*?)</span>', c)
        print(f"Card {i+1}: {title} ({len(tiles)} tiles)")
