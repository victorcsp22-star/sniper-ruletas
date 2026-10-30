import re

with open("lottobrasil_page.html", "r", encoding="utf-8") as f:
    html = f.read()

# Let's search for "bicho-hora" or cards
matches = re.findall(r'<div[^>]*class="[^"]*card[^"]*"[^>]*>.*?</div>\s*</div>', html, re.DOTALL)
print(f"Cards found: {len(matches)}")
for i, m in enumerate(matches[:5]):
    print(f"\n--- Card {i} ---")
    clean = re.sub(r'\s+', ' ', m)
    print(clean[:300])

# Let's also check all elements with id containing 'bicho' or 'hora' or 'resultado'
ids = re.findall(r'id="([^"]*)"', html)
interesting_ids = [i for i in ids if any(k in i.lower() for k in ['bicho', 'hora', 'sorteio', 'result', 'lotto', 'date', 'tab'])]
print("\nInteresting IDs:", interesting_ids)
