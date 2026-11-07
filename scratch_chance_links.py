import re

with open(r"C:\Users\victo\nuevas_ruletas\chance_home.html", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

print("Title:", re.findall(r'<title>(.*?)</title>', text))
links = re.findall(r'href=["\'](/loteria/[^"\']+)["\']', text)
for l in sorted(set(links)):
    print(l)
