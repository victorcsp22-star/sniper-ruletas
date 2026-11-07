import os
import sys

target = r"C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py"
static_target = r"C:\Users\victo\nuevas_ruletas\app_movil\static\server_zero_dep.py"

content = open(target, "r", encoding="utf-8").read()

blinded_fetch = '''def fetch_tuazar_html():
    """Descarga el HTML de TuAzar de forma 100% autonoma y blindada (Cero dependencia de PC)."""
    import subprocess
    import os
    import sys
    import time

    url = "https://www.tuazar.com/loteria/animalitos/resultados/"
    ua = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"

    # Lista de rutas absolutas infalibles para curl_static
    c_paths = [
        os.path.join(this_dir, "curl_static"),
        os.path.join(ROOT_DIR, "curl_static"),
        os.path.join(STATIC_DIR, "curl_static"),
        "/data/data/com.termux/files/home/sniper/curl_static",
        "/data/data/com.termux/files/home/curl_static",
        "./curl_static"
    ]

    valid_curl = None
    for cp in c_paths:
        if os.path.exists(cp) and os.path.getsize(cp) > 1000000:
            valid_curl = cp
            try:
                os.chmod(cp, 0o777)
            except Exception:
                pass
            break

    # Reintentos con retroceso: 3 intentos para evitar microcortes de datos móviles (4G)
    for intento in range(3):
        # 1. Prioridad: Binario Estático Autónomo
        if valid_curl:
            try:
                res = subprocess.run(
                    [valid_curl, "-k", "-s", "-L", "--connect-timeout", "6", "-m", "10", "-A", ua, url],
                    capture_output=True,
                    timeout=12
                )
                if res.returncode == 0 and len(res.stdout) > 2000:
                    return res.stdout.decode("utf-8", errors="ignore")
            except Exception:
                pass

        # 2. Windows PC (curl.exe nativo)
        if sys.platform == "win32":
            try:
                res = subprocess.run(
                    ["curl.exe", "-k", "-s", "-L", "--connect-timeout", "6", "-m", "10", "-A", ua, url],
                    capture_output=True,
                    timeout=12
                )
                if res.returncode == 0 and len(res.stdout) > 2000:
                    return res.stdout.decode("utf-8", errors="ignore")
            except Exception:
                pass

        # 3. urllib estándar si la librería SSL no está dañada
        try:
            import ssl
            import urllib.request
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(url, headers={"User-Agent": ua})
            with urllib.request.urlopen(req, context=ctx, timeout=8) as response:
                html = response.read().decode("utf-8", errors="ignore")
                if len(html) > 2000:
                    return html
        except Exception:
            pass

        time.sleep(1.5)

    return ""
'''

import re
pattern = r"def fetch_tuazar_html\(\):.*?return \"\"\s*\n"
content = re.sub(pattern, blinded_fetch + "\n", content, flags=re.DOTALL)

open(target, "w", encoding="utf-8").write(content)
open(static_target, "w", encoding="utf-8").write(content)
print("[+] server_zero_dep.py actualizado con reintentos y deteccion absoluta.")
