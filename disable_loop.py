import os

path = r"C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py"
with open(path, "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

# Desactivar start_background_auto_sync al final
old_main = """    start_background_auto_sync()
    server = ThreadingHTTPServer(("0.0.0.0", port), SniperHandler)"""

new_main = """    # Sincronización bajo demanda (Ahorro de batería y sin saturar red)
    print("[*] 🛡️ Modo Bajo Demanda Activado: Las actualizaciones se realizan al tocar 'TuAzar' en la app.")
    server = ThreadingHTTPServer(("0.0.0.0", port), SniperHandler)"""

if old_main in text:
    text = text.replace(old_main, new_main)
    print("start_background_auto_sync() desactivado con éxito.")
else:
    print("No se encontró old_main")

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
