import requests
import json
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "*/*"
}

# 1. Fetch main html to see scripts and endpoints
urls = [
    "https://lottobichos.com/sorteios/lottobrasil",
    "https://lottobichos.com/sorteios/lottobicho"
]

for url in urls:
    r = requests.get(url, headers=HEADERS, timeout=10)
    print(f"URL: {url} -> Status: {r.status_code}, Length: {len(r.text)}")
    # Find api endpoints or ajax urls
    matches = re.findall(r'https?://[^\s"\'<>]+(?:api|sorteio|resultado|json)[^\s"\'<>]*', r.text)
    print("API-like matches:", matches[:10])

# 2. Check common API routes on lottobichos.com
test_routes = [
    "https://lottobichos.com/api/sorteios",
    "https://lottobichos.com/api/resultados",
    "https://lottobichos.com/sorteios/lottobrasil/json",
    "https://lottobichos.com/sorteios/lottobrasil/data",
    "https://lottobichos.com/sorteios/api/lottobrasil",
    "https://lottobichos.com/api/lottobrasil",
    "https://lottobichos.com/sorteios"
]

print("\nProbando rutas comunes:")
for route in test_routes:
    try:
        resp = requests.get(route, headers=HEADERS, timeout=5)
        print(f"  {route} -> Status: {resp.status_code}, Type: {resp.headers.get('Content-Type')}, Len: {len(resp.text)}")
    except Exception as e:
        print(f"  {route} -> Error: {e}")
