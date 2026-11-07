import os
import re

path = r"C:\Users\victo\nuevas_ruletas\semana_test.html"
with open(path, "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

titles = re.findall(r'class=["\'][^"\']*lw-title[^"\']*["\'][^>]*>(.*?)<', text)
print(f"Total títulos en semana: {len(titles)}")
for t in sorted(set(t.strip() for t in titles if t.strip())):
    print(f"  * {t}")
