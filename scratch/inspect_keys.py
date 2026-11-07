import json

with open("audit_results.json", "r", encoding="utf-8") as f:
    d = json.load(f)

print("KEYS:", list(d.keys()))
for k in d.keys():
    if isinstance(d[k], dict):
        print(f"  {k} keys:", list(d[k].keys()))
    else:
        print(f"  {k} type:", type(d[k]))
