import urllib.request
import re

url = "https://www.tuazar.com/loteria/animalitos/resultados/"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=10) as r:
    html = r.read().decode("utf-8", errors="ignore")

cards = re.split(r'<div class="[^"]*lc-card[^"]*"', html)[1:]
for c in cards:
    m_title = re.search(r'<h3 class="lc-title"[^>]*>(.*?)</h3>', c, re.DOTALL)
    if not m_title: continue
    title = re.sub(r'<[^>]+>', '', m_title.group(1)).strip().lower()
    if "lotto activo" in title and "rd" not in title:
        tiles = re.split(r'<div class="[^"]*lc-tile[^"]*"', c)[1:]
        print(f"Lotto Activo has {len(tiles)} raw tiles")
        for t in tiles:
            if "lc-tile--empty" in t: continue
            m_time = re.search(r'class="lc-tile-time"[^>]*>(.*?)</div>', t, re.DOTALL)
            m_num = re.search(r'class="lc-tile-num"[^>]*>(.*?)</span>', t, re.DOTALL)
            m_anim = re.search(r'class="lc-tile-animal"[^>]*>(.*?)</span>', t, re.DOTALL)
            if m_time and m_num:
                hora = re.sub(r'<[^>]+>', '', m_time.group(1)).strip()
                num = re.sub(r'<[^>]+>', '', m_num.group(1)).strip()
                anim = re.sub(r'<[^>]+>', '', m_anim.group(1)).strip() if m_anim else ""
                print(f"   {hora}: #{num} {anim}")
