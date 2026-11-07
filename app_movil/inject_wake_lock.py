server_path = r"C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py"
static_path = r"C:\Users\victo\nuevas_ruletas\app_movil\static\server_zero_dep.py"

wake_lock_code = '''    # Activar wake-lock de Termux automaticamente para que no se duerma con la pantalla apagada
    try:
        import subprocess
        subprocess.run(["termux-wake-lock"], capture_output=True, timeout=2)
        print("[*] 🔒 Termux Wake-Lock activado (operación continua en segundo plano).")
    except Exception:
        pass
'''

for path in [server_path, static_path]:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    if "termux-wake-lock" not in text:
        target = '    start_background_auto_sync()\n'
        replacement = wake_lock_code + '    start_background_auto_sync()\n'
        text = text.replace(target, replacement)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"[+] Wake-lock inyectado en {path}")
    else:
        print(f"[*] Wake-lock ya presente en {path}")
