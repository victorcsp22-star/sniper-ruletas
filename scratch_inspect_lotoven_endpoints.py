import requests
import lxml.html

urls = [
    "https://lotoven.com/animalito/lottoactivordint/",
    "https://lotoven.com/animalito/lottoactivordominicana/"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

for u in urls:
    print("=" * 70)
    print("Consultando:", u)
    resp = requests.get(u, headers=headers, timeout=15)
    print("Status:", resp.status_code, "Longitud:", len(resp.text))
    doc = lxml.html.fromstring(resp.text)
    
    # Titulos
    h1 = doc.xpath("//h1//text()")
    h2 = doc.xpath("//h2//text()")
    print("H1:", [x.strip() for x in h1 if x.strip()])
    print("H2:", [x.strip() for x in h2 if x.strip()][:5])
    
    # Buscar calendarios, selectores de fechas o históricos
    dates_input = doc.xpath("//input[contains(@type, 'date') or contains(@name, 'date')]")
    print(f"Inputs de fecha: {len(dates_input)}")
    
    # Enlaces a fechas anteriores o paginadores
    history_links = [a.get("href") for a in doc.xpath("//a") if "date" in a.get("href", "") or "anterior" in a.get("href", "") or "historico" in a.get("href", "")]
    print("Enlaces históricos:", history_links[:5])

    # Extraer los primeros sorteos visibles
    # Buscar elementos con resultados (horas, animales, números)
    items = doc.xpath("//div[contains(@class, 'result') or contains(@class, 'draw') or contains(@class, 'item') or contains(@class, 'card')]")
    print(f"Elementos encontrados: {len(items)}")
    
    sample_text = " ".join(doc.text_content().split())
    # Buscar patrones de hora y animal
    print("Muestra de texto:", sample_text[sample_text.find("Resultados"):sample_text.find("Resultados")+500])
