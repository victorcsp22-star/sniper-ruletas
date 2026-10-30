import requests
import datetime
from concurrent.futures import ThreadPoolExecutor
import time

url = "https://lottobichos.com/sorteios/getsorteios"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}

def fetch_day(args):
    d_str, lotr = args
    try:
        r = requests.post(url, data={"date": d_str, "lotr": lotr}, headers=headers, timeout=10)
        if r.status_code == 200:
            js = r.json()
            data = js.get("data", {})
            key = list(data.keys())[0] if data else None
            return d_str, len(data.get(key, {}))
    except Exception:
        pass
    return d_str, 0

# Test 30 days
start_date = datetime.date(2026, 9, 1)
tasks = [( (start_date + datetime.timedelta(days=i)).strftime("%d-%m-%Y"), "lottbrasil") for i in range(30)]

t0 = time.time()
with ThreadPoolExecutor(max_workers=8) as ex:
    results = list(ex.map(fetch_day, tasks))
t1 = time.time()

print(f"Fetched {len(results)} days in {t1 - t0:.2f}s")
print("Sample results:", results[:5])
