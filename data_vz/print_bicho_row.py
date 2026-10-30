with open("lottobrasil_page.html", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find('bicho-mostra-row')
if idx != -1:
    print(text[idx-200 : idx+1500])
else:
    print("Not found")
