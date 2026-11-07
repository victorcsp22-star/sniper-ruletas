import urllib.request
import re

url = 'https://www.tuazar.com/loteria/animalitos/resultados/'
headers = {'User-Agent': 'Mozilla/5.0'}
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=10) as r:
    html = r.read().decode('utf-8', errors='ignore')

print('Fetched HTML size:', len(html))
cards = re.findall(r'<h3 class="lc-title"[^>]*>(.*?)</h3>', html)
print('Found lottery cards:', len(cards))
for c in cards[:7]:
    clean = re.sub(r'<[^>]+>', '', c).strip()
    print(' •', clean)
