import requests
import datetime

url = "https://lottobichos.com/sorteios/getsorteios"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}

test_dates = [
    "01-01-2022",
    "01-01-2023",
    "01-06-2023",
    "01-01-2024",
    "01-01-2025",
    "01-01-2026"
]

for d in test_dates:
    for lotr in ["lottbrasil", "bicho"]:
        r = requests.post(url, data={"date": d, "lotr": lotr}, headers=headers, timeout=5)
        try:
            js = r.json()
            data = js.get("data", {})
            key = list(data.keys())[0] if data else None
            draws = data.get(key, {}) if key else {}
            # count valid draws (not '--')
            valid = {h: v for h, v in draws.items() if v != '--'}
            print(f"Date: {d} | Lotr: {lotr} | Key: {key} | Valid draws: {len(valid)} / {len(draws)} | Sample: {valid}")
        except Exception as e:
            print(f"Date: {d} | Lotr: {lotr} | Error: {e}")
