import re

code = open(r'C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py', 'r', encoding='utf-8').read()
matches = re.findall(r'"([^"]+)":\s*\{\s*"file":\s*os\.path\.join\(ROOT_DIR,\s*"([^"]+)"\)', code)
for r, f in matches:
    print(f"{r:30} -> {f}")
