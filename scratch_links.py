import re

with open(r"C:\Users\victo\nuevas_ruletas\tuazar_test.html", "r", encoding="utf-8", errors="ignore") as f:
    html = f.read()

links = re.findall(r'href=["\'](/loteria/[^"\']+)["\']', html)
for l in sorted(set(links)):
    print(l)
