import re

with open(r"C:\Users\victo\nuevas_ruletas\tuazar_now.html", "r", encoding="utf-8", errors="ignore") as f:
    html = f.read()

blocks = [b for b in html.split('<div class="lc-card') if "granjazo" in b.lower()]
print(f"Bloques Granjazo encontrados: {len(blocks)}")
if blocks:
    b = blocks[0]
    tiles = re.split(r'class="lc-tile(?=[\s"])', b)
    print("Sorteos en tarjeta Granjazo en TuAzar hoy:")
    for t in tiles[1:]:
        if "lc-tile--empty" in t:
            continue
        m_t = re.search(r'class="lc-tile-time"[^>]*>(.*?)</div>', t)
        m_n = re.search(r'class="lc-tile-num"[^>]*>(.*?)</span>', t)
        m_a = re.search(r'class="lc-tile-name"[^>]*>(.*?)</div>', t)
        t_str = m_t.group(1).strip() if m_t else ""
        n_str = m_n.group(1).strip() if m_n else ""
        a_str = m_a.group(1).strip() if m_a else ""
        print(f"  * {t_str} | #{n_str} {a_str}")
