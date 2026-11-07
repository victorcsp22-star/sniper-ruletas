import urllib.request
import re

req = urllib.request.Request('https://www.tuazar.com/loteria/animalitos/resultados/', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
html = urllib.request.urlopen(req, timeout=12).read().decode('utf-8', errors='ignore')
print('HTML Length:', len(html))

# Check how cards are represented
cards = html.split('class="lc-card')
print('Cards count:', len(cards))
for c in cards[1:]:
    m_title = re.search(r'class="lc-title"[^>]*>(.*?)</h3>', c, re.DOTALL)
    if m_title:
        title = re.sub(r'<[^>]+>', '', m_title.group(1)).strip()
        print('Title:', title)
        # Check tiles
        tiles = c.split('class="lc-tile')
        print(f"  Tiles count: {len(tiles)}")
        # Split by individual tile, avoiding lc-tiles, lc-tile-img, lc-tile-time, etc.
        tiles = re.split(r'class="lc-tile(?=[\s"])', c)
        print(f"  Real tiles count: {len(tiles)}")
        for idx, t in enumerate(tiles[1:6]):
            if "lc-tile--empty" in t:
                print(f"    Tile #{idx}: EMPTY")
                continue
            m_time = re.search(r'class="lc-tile-time"[^>]*>(.*?)</div>', t, re.DOTALL)
            m_num = re.search(r'class="lc-tile-num"[^>]*>(.*?)</span>', t, re.DOTALL)
            m_anim = re.search(r'class="lc-tile-animal"[^>]*>(.*?)</span>', t, re.DOTALL)
            time_txt = re.sub(r'<[^>]+>', '', m_time.group(1)).strip() if m_time else "NO_TIME"
            num_txt = re.sub(r'<[^>]+>', '', m_num.group(1)).strip() if m_num else "NO_NUM"
            anim_txt = re.sub(r'<[^>]+>', '', m_anim.group(1)).strip() if m_anim else ""
            print(f"    Tile #{idx}: time={time_txt}, num={num_txt}, animal={anim_txt}")
        break
