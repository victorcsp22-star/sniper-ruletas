for fname in ["core.js", "web-bundle.js", "router-bundle.js", "geral-bundle.js"]:
    with open(fname, "r", encoding="utf-8") as f:
        c = f.read()
    idx = c.find('fetch_getSorteios=')
    if idx == -1:
        idx = c.find('fetch_getSorteios =')
    if idx != -1:
        print(f"Found assignment in {fname}:")
        print(c[idx : idx+1500])
