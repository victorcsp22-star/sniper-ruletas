import requests

url = "https://lottobichos.com/sorteios/lottobrasil"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}
r = requests.get(url, headers=headers)

with open("lottobrasil_page.html", "w", encoding="utf-8") as f:
    f.write(r.text)

print("Saved HTML, length:", len(r.text))
