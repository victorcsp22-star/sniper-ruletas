import requests

url = "https://lottobichos.com/sorteios/getsorteios"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}

for m in [1, 3, 6, 9, 10, 11, 12]:
    d = f"01-{m:02d}-2022"
    r = requests.post(url, data={"date": d, "lotr": "lottbrasil"}, headers=headers, timeout=5)
    print(f"2022-{m:02d}-01 -> Status {r.status_code}, Len {len(r.text)}")
