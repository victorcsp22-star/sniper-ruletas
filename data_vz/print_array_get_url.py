with open("core.js", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find('arrayGetUrlLocalStorage')
if idx != -1:
    print(text[idx : idx+800])
else:
    print("arrayGetUrlLocalStorage not found")
