with open("core.js", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find('requireApp')
if idx != -1:
    print(text[max(0, idx-100) : min(len(text), idx+1000)])
else:
    print("requireApp not found")
