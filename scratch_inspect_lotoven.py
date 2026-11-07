import requests
import lxml.html
import re

url = "https://lotoven.com/animalitos-internacional"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}
resp = requests.get(url, headers=headers, timeout=15)
doc = lxml.html.fromstring(resp.text)

print("=== ENLACES ===")
for a in doc.xpath("//a"):
    href = a.get("href", "")
    text = " ".join(a.text_content().split())
    if any(k in href.lower() or k in text.lower() for k in ["animal", "lotto", "rd", "internacional", "ruleta", "granj"]):
        print(f"[{text}] -> {href}")

print("\n=== TEXTO DEL CUERPO (SECCIONES PRINCIPALES) ===")
# Extraer divs principales
cards = doc.xpath('//div[contains(@class, "card") or contains(@class, "item") or contains(@class, "lottery")]')
print(f"Cards encontradas: {len(cards)}")

# Buscar tablas
tables = doc.xpath("//table")
print(f"Tablas encontradas: {len(tables)}")
for i, t in enumerate(tables):
    print(f"Tabla {i}:", " ".join(t.text_content().split())[:200])

# Buscar cualquier mención de loterías
text_all = doc.text_content()
for line in text_all.splitlines():
    line_clean = " ".join(line.split())
    if any(k in line_clean.lower() for k in ["lotto activo rd", "rd internacional", "internacional"]):
        print("Mención encontrada:", line_clean[:150])
