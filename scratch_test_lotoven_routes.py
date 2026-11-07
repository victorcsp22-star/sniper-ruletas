import requests
import lxml.html

variants = [
    "https://lotoven.com/animalitos-internacional?fecha=2026-10-15",
    "https://lotoven.com/animalitos-internacional/2026-10-15",
    "https://lotoven.com/animalito/lottoactivordominicana?fecha=2026-10-15",
    "https://lotoven.com/animalito/lottoactivordominicana/2026-10-15/",
    "https://lotoven.com/animalito/lottoactivordint/2026-10-15/",
    "https://lotoven.com/animalito/lottoactivordint?fecha=2026-10-15",
    "https://lotoven.com/resultados/animalitos-internacional/2026-10-15",
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

for u in variants:
    resp = requests.get(u, headers=headers, timeout=10)
    print(f"URL: {u}")
    print(f"  Status: {resp.status_code}")
    if resp.status_code == 200:
        doc = lxml.html.fromstring(resp.text)
        inp = doc.xpath('//input[@name="fecha"]')
        val = inp[0].get("value") if inp else "No input"
        print(f"  Input fecha value: {val}")
        # Buscar fecha visible en el texto
        txt = " ".join(doc.text_content().split())
        if "15 de October" in txt or "2026-10-15" in txt or "Thursday" in txt or "Jueves" in txt:
            print("  [✓] ENCONTRADA FECHA 15 DE OCTUBRE!")
