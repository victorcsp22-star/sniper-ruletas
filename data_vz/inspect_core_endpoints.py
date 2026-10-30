import re

with open("core.js", "r", encoding="utf-8") as f:
    code = f.read()

# Let's find all occurrences of .fetch_ or url: or /
matches = re.finditer(r'url\s*:\s*([^,}]+)', code)
for m in matches:
    print("URL target:", m.group(0))

# Search for any string containing urlS or window.GB
gb_calls = re.findall(r'window\.GB\.[a-zA-Z0-9_.]+', code)
print("\nGB accesses:", set(gb_calls))

# Search for datepicker or date change event
dp_matches = re.findall(r'.{0,40}datepicker.{0,40}', code, re.I)
print("\nDatepicker matches:", len(dp_matches))
for dm in dp_matches[:5]:
    print(" ", dm.strip())
