import os
import zipfile
import shutil

root_dir = r"C:\Users\victo\nuevas_ruletas"
app_movil_dir = os.path.join(root_dir, "app_movil")
static_dir = os.path.join(app_movil_dir, "static")
output_zip = os.path.join(static_dir, "sniper_termux_clean.zip")

server_file = os.path.join(app_movil_dir, "server_zero_dep.py")

files_to_pack = [
    (server_file, "server_zero_dep.py"),
    (server_file, "app_movil/server_zero_dep.py"),
    (os.path.join(static_dir, "curl_static"), "curl_static"),
    (os.path.join(root_dir, "data_vz", "lotto_activo_2anios.csv"), "data_vz/lotto_activo_2anios.csv"),
    (os.path.join(root_dir, "data_vz", "guacharo_activo_2anios.csv"), "data_vz/guacharo_activo_2anios.csv"),
    (os.path.join(root_dir, "data_vz", "ruleta_royal_2anios.csv"), "data_vz/ruleta_royal_2anios.csv"),
    (os.path.join(root_dir, "monje_millonario.csv"), "monje_millonario.csv"),
    (os.path.join(root_dir, "gatazo.csv"), "gatazo.csv"),
    (os.path.join(root_dir, "lotto_gato.csv"), "lotto_gato.csv"),
    (os.path.join(root_dir, "mega_animal_40.csv"), "mega_animal_40.csv"),
    (os.path.join(root_dir, "granja_millonaria_granjazo.csv"), "granja_millonaria_granjazo.csv"),
    (os.path.join(root_dir, "loto_chaima.csv"), "loto_chaima.csv"),
    (os.path.join(root_dir, "ledger_nuevas_ruletas.csv"), "ledger_nuevas_ruletas.csv"),
    (os.path.join(root_dir, "state_nuevas_ruletas.json"), "state_nuevas_ruletas.json"),
    (os.path.join(static_dir, "index.html"), "static/index.html"),
    (os.path.join(static_dir, "index.html"), "index.html"),
    (os.path.join(static_dir, "manifest.json"), "static/manifest.json"),
    (os.path.join(static_dir, "service-worker.js"), "static/service-worker.js"),
    (os.path.join(static_dir, "icon-192.png"), "static/icon-192.png"),
    (os.path.join(static_dir, "icon-512.png"), "static/icon-512.png"),
]

with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as z:
    for src, arc in files_to_pack:
        if os.path.exists(src):
            z.write(src, arc)
            print(f"[+] Empaquetado: {arc} ({os.path.getsize(src)} bytes)")
        else:
            print(f"[-] ADVERTENCIA: no se encontro {src}")

shutil.copyfile(output_zip, os.path.join(root_dir, "sniper_termux_clean.zip"))
print(f"\n[OK] Zip generado y copiado con éxito: ({os.path.getsize(output_zip)} bytes)")
