for fname in ["core.js", "web-bundle.js", "router-bundle.js", "lottobrasil_page.html"]:
    with open(fname, "r", encoding="utf-8") as f:
        c = f.read()
    idx = c.find('fetch_getSorteios')
    if idx != -1:
        print(f"Found fetch_getSorteios in {fname}:")
        print(c[idx-50 : idx+1500])
