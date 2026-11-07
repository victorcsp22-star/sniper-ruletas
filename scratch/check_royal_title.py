import urllib.request
import re

req = urllib.request.Request('https://www.tuazar.com/loteria/animalitos/resultados/', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
html = urllib.request.urlopen(req, timeout=12).read().decode('utf-8', errors='ignore')

for c in html.split('class="lc-card')[1:]:
    m_title = re.search(r'class="lc-title"[^>]*>(.*?)</h3>', c, re.DOTALL)
    if m_title and 'royal' in m_title.group(1).lower():
        title = re.sub(r'<[^>]+>', '', m_title.group(1)).strip()
        print("Card title found in HTML:", repr(title))
