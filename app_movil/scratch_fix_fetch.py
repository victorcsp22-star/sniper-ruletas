import sys
import os

target_path = r"C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py"
with open(target_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Corregir endpoint tuazar_bridge
if '["curl.exe", "-k"' in content:
    content = content.replace('["curl.exe", "-k"', '[("curl.exe" if sys.platform == "win32" else "curl"), "-k"')
    print("[+] Endpoint /api/tuazar_bridge corregido.")

# 2. Corregir urllib como primer mecanismo en fetch_tuazar_html
urllib_primary = '''def fetch_tuazar_html():
    """Descarga el HTML de TuAzar de forma 100% autonoma desde el celular (Cero dependencia de PC)."""
    import subprocess
    import os
    import sys
    import urllib.request
    import ssl

    url = "https://www.tuazar.com/loteria/animalitos/resultados/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # 1. urllib nativo de Python con bypass SSL (máxima compatibilidad sin invocar procesos externos)
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as response:
            html = response.read().decode("utf-8", errors="ignore")
            if len(html) > 2000:
                return html
    except Exception:
        pass

    # 2. Curl Estático Embebido (para Android Termux)
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
                    [c_path, "-k", "-s", "-L", "-A", headers["User-Agent"], url],
                    capture_output=True,
                    timeout=10
                )
                if res.returncode == 0 and len(res.stdout) > 2000:
                    return res.stdout.decode("utf-8", errors="ignore")
            except Exception:
                pass

    # 3. Curl de sistema agnóstico (curl.exe en Windows, curl en Android/Linux)
    curl_sys = "curl.exe" if sys.platform == "win32" else "curl"
    try:
        res = subprocess.run(
            [curl_sys, "-k", "-s", "-L", "-A", headers["User-Agent"], url],
            capture_output=True,
            timeout=10
        )
        if res.returncode == 0 and len(res.stdout) > 2000:
            return res.stdout.decode("utf-8", errors="ignore")
    except Exception:
        pass

    # 4. Wget Nativo si existe
    try:
        res = subprocess.run(
            ["wget", "--no-check-certificate", "-qO-", f"--user-agent={headers['User-Agent']}", url],
            capture_output=True,
            timeout=10
        )
        if res.returncode == 0 and len(res.stdout) > 2000:
            return res.stdout.decode("utf-8", errors="ignore")
    except Exception:
        pass

    # 5. Puente LAN si estuviese disponible
    for bridge_host in ["192.168.1.2:5000", "10.2.0.2:5000", "127.0.0.1:5000"]:
        try:
            pc_url = f"http://{bridge_host}/api/tuazar_bridge"
            with urllib.request.urlopen(pc_url, timeout=1) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                if len(html) > 2000:
                    return html
        except Exception:
            pass

    return ""
'''

# Sustituir la función fetch_tuazar_html completa
import re
pattern = r"def fetch_tuazar_html\(\):.*?return \"\"\s*\n"
content = re.sub(pattern, urllib_primary + "\n", content, flags=re.DOTALL)

with open(target_path, "w", encoding="utf-8") as f:
    f.write(content)

# Copiar a static/server_zero_dep.py
static_srv = r"C:\Users\victo\nuevas_ruletas\app_movil\static\server_zero_dep.py"
with open(static_srv, "w", encoding="utf-8") as f:
    f.write(content)

print("[+] Archivos actualizados con éxito.")
