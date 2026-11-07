import requests
import lxml.html

url = "https://lotoven.com/animalitos-internacional"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}
resp = requests.get(url, headers=headers, timeout=15)
doc = lxml.html.fromstring(resp.text)

# Imprimir todas las secciones y sus contenidos
for elem in doc.xpath("//div[contains(@class, 'container')]"):
    t = " ".join(elem.text_content().split())
    if len(t) > 20:
        print("CONTAINER:", t[:250])
        print("-" * 50)
