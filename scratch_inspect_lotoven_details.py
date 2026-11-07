import requests
import lxml.html

urls = [
    ("RD Int", "https://lotoven.com/animalito/lottoactivordint/"),
    ("RDominicana", "https://lotoven.com/animalito/lottoactivordominicana/")
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

for name, u in urls:
    print("=" * 70)
    print("Nombre:", name)
    resp = requests.get(u, headers=headers, timeout=15)
    doc = lxml.html.fromstring(resp.text)
    
    # Buscar todos los textos que contengan AM o PM
    text_blocks = doc.xpath("//*[contains(text(), 'AM') or contains(text(), 'PM')]")
    print(f"Bloques con horario: {len(text_blocks)}")
    for b in text_blocks[:15]:
        print("  ->", b.tag, b.get("class", ""), ":", b.text_content().strip())

    # Ver si hay formularios o llamadas a API (AJAX/Fetch)
    scripts = doc.xpath("//script")
    print(f"Scripts en la página: {len(scripts)}")
    for s in scripts:
        t = s.text_content()
        if "ajax" in t.lower() or "fetch" in t.lower() or "api" in t.lower() or "date" in t.lower() or "resultado" in t.lower():
            for line in t.splitlines():
                if any(w in line.lower() for w in ["url", "api", "load", "get", "post", "date"]):
                    print("    script line:", line.strip()[:100])
