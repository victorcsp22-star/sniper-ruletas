for name in ["geral-bundle.js", "web-bundle.js", "router-bundle.js"]:
    print(f"\n=================== {name} ===================")
    with open(name, "r", encoding="utf-8") as f:
        content = f.read()
    print(f"Length: {len(content)}")
    print(content[:2000])
