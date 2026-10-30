with open("core.js", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find('var _fetch_=function')
if idx != -1:
    print(text[idx : idx+1200])
else:
    print("_fetch_ definition not found")
