import re

server_path = r"C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py"
static_server_path = r"C:\Users\victo\nuevas_ruletas\app_movil\static\server_zero_dep.py"

for path in [server_path, static_server_path]:
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()

    # Reemplazar la condicion de filtro historico por filtro estricto del dia actual
    old_cond = 'if fec in [date_str, "2026-11-01", "2026-11-02"] or not fec:'
    new_cond = 'if fec == date_str:'

    if old_cond in code:
        code = code.replace(old_cond, new_cond)
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"[+] Limpieza diaria estricta aplicada con exito en {path}")
    else:
        # Intento con regex
        pattern = r'if\s+fec\s+in\s+\[date_str,.*?\]\s+or\s+not\s+fec:'
        if re.search(pattern, code):
            code = re.sub(pattern, 'if fec == date_str:', code)
            with open(path, "w", encoding="utf-8") as f:
                f.write(code)
            print(f"[+] Limpieza diaria estricta aplicada con regex en {path}")
        else:
            print(f"[-] No se encontro condicion anterior en {path}")
