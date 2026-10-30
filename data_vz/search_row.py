with open("lottobrasil_page.html", "r", encoding="utf-8") as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'bicho-mostra-row', text)]
print("Occurrences of bicho-mostra-row in page:", len(matches))
for pos in matches:
    print("--- Occurrence at", pos, "---")
    print(text[max(0, pos-100) : min(len(text), pos+300)])
