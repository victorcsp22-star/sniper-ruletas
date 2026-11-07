import os
import re

path = r"C:\Users\victo\nuevas_ruletas\tuazar_test.html"
with open(path, "r", encoding="utf-8", errors="ignore") as f:
    html = f.read()

print(f"Tamano HTML: {len(html)} caracteres")

# Buscar todas las clases results-title o similares
titles = re.findall(r'<h\d[^>]*>(.*?)</h\d>', html, re.DOTALL)
clean_titles = set()
for t in titles:
    c = re.sub(r'<[^>]+>', '', t).strip()
    if c:
        clean_titles.add(c)

print("\n--- TITULOS ENCONTRADOS EN TUAZAR HOY ---")
for t in sorted(clean_titles):
    print(f"  * {t}")

keywords = ["chance", "arrejuntao", "bichitos", "fueras", "fieras", "mascotas", "fauna"]
print("\n--- BUSQUEDA DE PALABRAS CLAVE ---")
for kw in keywords:
    matches = [m.strip() for m in re.findall(rf'[^<\n]{{0,40}}{kw}[^>\n]{{0,40}}', html, re.IGNORECASE)]
    print(f"Clave '{kw}': {len(matches)} coincidencias")
    for m in set(matches[:5]):
        print(f"   -> {m}")
