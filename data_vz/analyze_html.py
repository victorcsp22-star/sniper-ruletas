import re

with open("lottobrasil_page.html", "r", encoding="utf-8") as f:
    html = f.read()

# Let's find all script tags and print their first lines and lengths
scripts = re.findall(r'<script(.*?)>(.*?)</script>', html, re.DOTALL)
print(f"Total scripts found: {len(scripts)}")
for i, (attr, body) in enumerate(scripts):
    print(f"\n--- Script {i} (attrs: {attr.strip()}, len: {len(body)}) ---")
    lines = body.strip().split('\n')
    for l in lines[:5]:
        print("  ", l[:120])
    if len(lines) > 5:
        print("   ... [lines omitted] ...")
        for l in lines[-3:]:
            print("  ", l[:120])

# Let's search for "sorteio" in the non-script HTML
no_scripts = re.sub(r'<script.*?</script>', '', html, flags=re.DOTALL)
sorteios_mentions = re.findall(r'.{0,50}sorteio.{0,50}', no_scripts, re.I)
print(f"\nSorteio mentions in body: {len(sorteios_mentions)}")
for sm in sorteios_mentions[:10]:
    print("  ->", sm.strip())
