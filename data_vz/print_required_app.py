import re

with open("lottobrasil_page.html", "r", encoding="utf-8") as f:
    html = f.read()

m = re.search(r'<script[^>]*id="requiredAppJS"[^>]*>(.*?)</script>', html, re.DOTALL)
if m:
    print("=== requiredAppJS ===")
    print(m.group(1))
