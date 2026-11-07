import os
import zipfile
import shutil

ROOT_DIR = r"C:\Users\victo\nuevas_ruletas"
ZIP_PATH = os.path.join(ROOT_DIR, "app_movil", "static", "sniper_ruletas.zip")
DOWNLOADS_ZIP = os.path.expanduser(r"~\Downloads\sniper_ruletas.zip")

print("Empaquetando sniper_ruletas.zip con servidor cero-dependencias...")

# Archivos a incluir:
# 1. config.py, state_nuevas_ruletas.json, ledger_nuevas_ruletas.csv, diario_nuevas_ruletas.md
# 2. Toda la carpeta data_vz
# 3. Toda la carpeta app_movil
# 4. CSVs de la raíz: gatazo.csv, mega_animal_40.csv, monje_millonario.csv

with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
    # Raíz
    for fname in ["config.py", "state_nuevas_ruletas.json", "ledger_nuevas_ruletas.csv", "diario_nuevas_ruletas.md", "gatazo.csv", "mega_animal_40.csv", "monje_millonario.csv"]:
        fpath = os.path.join(ROOT_DIR, fname)
        if os.path.exists(fpath):
            zipf.write(fpath, fname)
            print(f"  + {fname}")

    # data_vz
    data_vz_dir = os.path.join(ROOT_DIR, "data_vz")
    for root, dirs, files in os.walk(data_vz_dir):
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, ROOT_DIR)
            zipf.write(full, rel)

    # app_movil
    app_movil_dir = os.path.join(ROOT_DIR, "app_movil")
    for root, dirs, files in os.walk(app_movil_dir):
        if "__pycache__" in root:
            continue
        for f in files:
            if f.endswith(".zip"):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, ROOT_DIR)
            zipf.write(full, rel)
            print(f"  + {rel}")

shutil.copy2(ZIP_PATH, DOWNLOADS_ZIP)
print(f"Zip creado exitosamente en {ZIP_PATH} ({os.path.getsize(ZIP_PATH)} bytes)")
print(f"Copiado a Downloads: {DOWNLOADS_ZIP}")
