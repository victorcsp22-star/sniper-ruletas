import urllib.request
import re

req = urllib.request.Request('https://www.tuazar.com/loteria/animalitos/resultados/', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
html = urllib.request.urlopen(req, timeout=12).read().decode('utf-8', errors='ignore')

for c in html.split('class="lc-card'):
    if 'royal' in c.lower():
        tiles = re.split(r'class="lc-tile(?=[\s"])', c)
        print("Encontrada Ruleta Royal. Sorteos publicados:")
        for t in tiles[1:]:
            m_time = re.search(r'class="lc-tile-time"[^>]*>(.*?)</div>', t, re.DOTALL)
            m_num = re.search(r'class="lc-tile-num"[^>]*>(.*?)</span>', t, re.DOTALL)
            m_anim = re.search(r'class="lc-tile-animal"[^>]*>(.*?)</span>', t, re.DOTALL)
            time_txt = re.sub(r'<[^>]+>', '', m_time.group(1)).strip() if m_time else "---"
            num_txt = re.sub(r'<[^>]+>', '', m_num.group(1)).strip() if m_num else "---"
            anim_txt = re.sub(r'<[^>]+>', '', m_anim.group(1)).strip() if m_anim else "---"
            if "lc-tile--empty" in t:
                print(f"  Hora {time_txt}: [VACÍO / PENDIENTE]")
            else:
                print(f"  Hora {time_txt}: #{num_txt} {anim_txt}")
