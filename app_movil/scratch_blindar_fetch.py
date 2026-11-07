import os
import sys

target = r"C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py"
static_target = r"C:\Users\victo\nuevas_ruletas\app_movil\static\server_zero_dep.py"

content = open(target, "r", encoding="utf-8").read()

new_fetch = '''def fetch_tuazar_html():
    """Descarga el HTML de TuAzar de forma 100% autonoma desde el celular (Cero dependencia de PC)."""
    import subprocess
    import os
    import sys

    url = "https://www.tuazar.com/loteria/animalitos/resultados/"
    ua = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"

    # 1. Prioridad Absoluta: Binario Estático Autónomo (NO usa libcurl.so ni OpenSSL de Android/Termux)
    curl_candidates = [
        os.path.join(this_dir, "curl_static"),
        os.path.join(ROOT_DIR, "curl_static"),
        os.path.join(STATIC_DIR, "curl_static"),
        "./curl_static",
        "/data/data/com.termux/files/home/sniper/curl_static",
    ]
    for c_path in curl_candidates:
        if os.path.exists(c_path):
            try:
                try:
                    os.chmod(c_path, 0o777)
                except Exception:
                    pass
                res = subprocess.run(
                    [c_path, "-k", "-s", "-L", "-A", ua, url],
                    capture_output=True,
                    timeout=10
                )
                if res.returncode == 0 and len(res.stdout) > 2000:
                    return res.stdout.decode("utf-8", errors="ignore")
            except Exception:
                pass

    # 2. Curl de sistema agnóstico (en Windows usa curl.exe nativo sin problemas de libcurl)
    if sys.platform == "win32":
        try:
            res = subprocess.run(
                ["curl.exe", "-k", "-s", "-L", "-A", ua, url],
                capture_output=True,
                timeout=10
            )
            if res.returncode == 0 and len(res.stdout) > 2000:
                return res.stdout.decode("utf-8", errors="ignore")
        except Exception:
            pass

    # 3. urllib estándar solo si no falló previamente la librería SSL dinámica
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

    # 4. Wget nativo si existe
    try:
        res = subprocess.run(
            ["wget", "--no-check-certificate", "-qO-", f"--user-agent={ua}", url],
            capture_output=True,
            timeout=10
        )
        if res.returncode == 0 and len(res.stdout) > 2000:
            return res.stdout.decode("utf-8", errors="ignore")
    except Exception:
        pass

    return ""
'''

import re
pattern = r"def fetch_tuazar_html\(\):.*?return \"\"\s*\n"
content = re.sub(pattern, new_fetch + "\n", content, flags=re.DOTALL)

open(target, "w", encoding="utf-8").write(content)
open(static_target, "w", encoding="utf-8").write(content)
print("[+] server_zero_dep.py blindado para curl_static primero.")
