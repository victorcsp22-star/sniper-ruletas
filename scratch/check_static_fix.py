with open(r'C:\Users\victo\nuevas_ruletas\app_movil\static\server_zero_dep.py', encoding='utf-8') as f:
    s = f.read()
print("Has lookahead regex:", '(?=[\\s"])' in s)
print("File length:", len(s))
