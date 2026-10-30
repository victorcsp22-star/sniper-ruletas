import requests
import re

base = "https://lottobichos.com"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

for js in ["/assets/js/geral-bundle.js", "/assets/js/mybabel-bundle.js"]:
    url = base + js
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print(f"\n=== {js} (Status {r.status_code}, Len {len(r.text)}) ===")
        # Search for URLs or endpoints
        endpoints = set(re.findall(r'["\'](/[^"\']*sorteio[^"\']*)["\']', r.text, re.I))
        endpoints.update(re.findall(r'["\'](/[^"\']*resultado[^"\']*)["\']', r.text, re.I))
        endpoints.update(re.findall(r'["\'](/[^"\']*api[^"\']*)["\']', r.text, re.I))
        endpoints.update(re.findall(r'["\'](/[^"\']*data[^"\']*)["\']', r.text, re.I))
        print("Endpoints found:", list(endpoints)[:20])

        # Search for POST or GET requests
        ajax_patterns = re.findall(r'(?:fetch|axios|\$\.ajax|\$\.get|\$\.post)\s*\(([^)]+)\)', r.text)
        print("Ajax calls sample:", ajax_patterns[:10])

        # Search for lottobrasil or lottobicho mentions
        lotto_refs = re.findall(r'[^\n;]{0,50}(?:lottobrasil|lottobicho)[^\n;]{0,50}', r.text)
        print("Lotto refs count:", len(lotto_refs))
        for ref in lotto_refs[:10]:
            print("  Ref:", ref.strip())
            
    except Exception as e:
        print(f"Error {js}: {e}")
