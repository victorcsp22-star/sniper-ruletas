import re

for path in [r"C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py", r"C:\Users\victo\nuevas_ruletas\app_movil\static\server_zero_dep.py"]:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Reemplazar la funcion sync_from_pc por pass para evitar timeouts
    pattern = r"def sync_from_pc\(\):.*?(?=class SniperHandler)"
    replacement = "def sync_from_pc():\n    \"\"\"Modo 100% Autonomo: no bloquea esperando por ninguna PC.\"\"\"\n    pass\n\n\n"
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Modificado: {path}")

# Regenerar zip
import shutil, os, zipfile
base_dir = r"C:\Users\victo\nuevas_ruletas"
zip_path = os.path.join(base_dir, "app_movil", "static", "sniper_ruletas.zip")
files_to_pack = [
    ("config.py", os.path.join(base_dir, "config.py")),
    ("bot_nuevas_ruletas.py", os.path.join(base_dir, "bot_nuevas_ruletas.py")),
    ("live_auditor_engine.py", os.path.join(base_dir, "live_auditor_engine.py")),
    ("state_nuevas_ruletas.json", os.path.join(base_dir, "state_nuevas_ruletas.json")),
    ("ledger_nuevas_ruletas.csv", os.path.join(base_dir, "ledger_nuevas_ruletas.csv")),
    ("server_zero_dep.py", os.path.join(base_dir, "app_movil", "server_zero_dep.py")),
    ("reporte_horario.py", os.path.join(base_dir, "app_movil", "reporte_horario.py")),
]
data_dir = os.path.join(base_dir, "data_vz")
csv_files = [(os.path.join("data_vz", f), os.path.join(data_dir, f)) for f in os.listdir(data_dir) if f.endswith(".csv")]
static_dir = os.path.join(base_dir, "app_movil", "static")
static_files = [(os.path.join("static", f), os.path.join(static_dir, f)) for f in os.listdir(static_dir) if f != "sniper_ruletas.zip" and not os.path.isdir(os.path.join(static_dir, f))]

with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for arcname, realpath in (files_to_pack + csv_files + static_files):
        if os.path.exists(realpath) and os.path.isfile(realpath):
            z.write(realpath, arcname)

shutil.copy2(zip_path, os.path.join(static_dir, "static", "sniper_ruletas.zip"))
print("Zip maestro regenerado con éxito.")
