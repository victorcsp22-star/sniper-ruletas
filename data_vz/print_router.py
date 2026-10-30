with open("router-bundle.js", "r", encoding="utf-8") as f:
    text = f.read()

print("Length router-bundle:", len(text))
# Let's search for sorteios_get and lott_web
idx = text.find('sorteios_get')
print(text[idx-200 : idx+2000])
