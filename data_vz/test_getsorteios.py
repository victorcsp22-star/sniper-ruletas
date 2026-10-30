import requests
import json

url = "https://lottobichos.com/sorteios/getsorteios"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}

# Test 1: lottobrasil today or recent date
payloads = [
    {"date": "14-10-2026", "lotr": "lottbrasil"},
    {"date": "13-10-2026", "lotr": "lottbrasil"},
    {"date": "10-10-2026", "lotr": "bicho"},
    {"date": "14-10-2024", "lotr": "lottbrasil"},
    {"date": "14-10-2023", "lotr": "lottbrasil"},
]

for p in payloads:
    # Remember _fetch_ appends each item in data:
    # t.data.forEach(function(e){ for(var n in e) o.append(n, e[n]) })
    # which results in standard form-data: date=...&lotr=...
    r = requests.post(url, data=p, headers=headers)
    print(f"Query {p} -> Status {r.status_code}, Len {len(r.text)}")
    try:
        data = r.json()
        print("  Status key:", data.get("status"))
        print("  Data sample:", str(data.get("data"))[:300])
    except Exception as e:
        print("  Non-json response:", r.text[:200])
