import requests

base = "https://lottobichos.com"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

test_files = [
    "/assets/js/jquery-2.2.2.min.js",
    "/assets/css/web-style.css",
    "/assets/css/geral-style.css",
    "/assets/vanillajs-datepicker-master/dist/js/datepicker-full.min.js",
    "/assets/js/web-bundle.js",
    "/assets/js/router-bundle.js",
    "/assets/js/mybabel-bundle.js",
    "/assets/js/core-bundle.js",
    "/assets/js/geral-bundle.js",
    "/assets/bundle.js",
    "/assets/app.js",
    "/assets/main.js"
]

for tf in test_files:
    r = requests.get(base + tf, headers=headers)
    print(f"{tf} -> {r.status_code} ({len(r.text)} bytes)")
