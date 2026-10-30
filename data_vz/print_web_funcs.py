with open("web-bundle.js", "r", encoding="utf-8") as f:
    text = f.read()

print("Length web-bundle:", len(text))
for kw in ['sorteios_get', 'lott_web']:
    idx = text.find(kw)
    if idx != -1:
        print(f"\n=== {kw} ===")
        print(text[idx-50 : idx+1500])
    else:
        print(f"{kw} not found in web-bundle.js")
