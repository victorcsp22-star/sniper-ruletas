import urllib.request
import re

url = "https://tuazar.com/loteria/animalitos/"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    
    links = re.findall(r'href=["\'](/loteria/animalitos/[^"\']+)["\']', html)
    print("Links unicos encontrados:")
    for l in sorted(list(set(links))):
        print(l)
        
    print("\nTitulos o textos encontrados:")
    titles = re.findall(r'<h[234][^>]*>(.*?)</h[234]>', html, re.DOTALL)
    for t in titles:
        clean = re.sub(r'<[^>]+>', '', t).strip()
        if clean:
            print("-", clean)
except Exception as e:
    print("Error:", e)
