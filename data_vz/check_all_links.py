import requests
import lxml.html

HEADERS = {"User-Agent": "Mozilla/5.0"}
r = requests.get('https://www.tuazar.com/loteria/animalitos/resultados/', headers=HEADERS, timeout=12)
doc = lxml.html.fromstring(r.text)

# Search all links with /animalitos/ or lottery names
links = doc.xpath('//a[contains(@href, "animalitos")]')
print("Total enlaces de animalitos:", len(links))
found = set()
for l in links:
    text = l.text_content().strip()
    href = l.get('href', '')
    if text and text not in found:
        found.add(text)
        print(f"  {text} -> {href}")
