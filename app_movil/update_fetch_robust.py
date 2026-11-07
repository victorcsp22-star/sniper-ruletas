import urllib.request
import re

server_path = r"C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py"
with open(server_path, "r", encoding="utf-8") as f:
    text = f.read()

# fetch_tuazar_html perfeccionado:
# Si esta en Termux y tiene permisos, ejecuta chmod +x a curl_static si existe
new_fetch_func = '''def fetch_tuazar_html():
    """Descarga el HTML de TuAzar con sextuple redundancia autonoma total."""
    import subprocess
    import os

    # 1. PC Bridge (si la PC esta prendida en la misma red Wi-Fi)
    for bridge_host in ["192.168.1.2:5000", "10.2.0.2:5000", "127.0.0.1:5000"]:
        try:
            pc_url = f"http://{bridge_host}/api/tuazar_bridge"
            with urllib.request.urlopen(pc_url, timeout=2) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                if len(html) > 2000:
                    print(f"[+] TuAzar sincronizado via PC Bridge ({bridge_host}).")
                    return html
        except Exception:
            pass

    url = "https://www.tuazar.com/loteria/animalitos/resultados/"

    # 2. Curl Estatico Independiente (Binario musl aarch64 sin dependencias de OpenSSL de Android/Termux)
    curl_candidates = [
        "./curl_static",
        "./static/curl_static",
        "/data/data/com.termux/files/home/sniper/curl_static",
        os.path.join(STATIC_DIR, "curl_static"),
        os.path.join(ROOT_DIR, "curl_static")
    ]
    for c_path in curl_candidates:
        if os.path.exists(c_path):
            try:
                # Asegurar permisos de ejecucion
                try:
                    os.chmod(c_path, 0o777)
                except Exception:
                    pass
                res = subprocess.run(
                    [c_path, "-k", "-s", "-L", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", url],
                    capture_output=True,
                    timeout=12
                )
                if res.returncode == 0 and len(res.stdout) > 2000:
                    print("[+] TuAzar descargado via curl_static 100% autonomo.")
                    return res.stdout.decode("utf-8", errors="ignore")
            except Exception as e:
                pass

    # 3. Wget nativo de Android / Busybox (sin depender de OpenSSL de python)
    try:
        res = subprocess.run(
            ["wget", "--no-check-certificate", "-qO-", "--user-agent=Mozilla/5.0", url],
            capture_output=True,
            timeout=10
        )
        if res.returncode == 0 and len(res.stdout) > 2000:
            print("[+] TuAzar descargado via wget.")
            return res.stdout.decode("utf-8", errors="ignore")
    except Exception:
        pass

    # 4. Curl de sistema con bypass
    try:
        res = subprocess.run(
            ["curl", "-k", "-s", "-L", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", url],
            capture_output=True,
            timeout=10
        )
        if res.returncode == 0 and len(res.stdout) > 2000:
            print("[+] TuAzar descargado via curl sistema.")
            return res.stdout.decode("utf-8", errors="ignore")
    except Exception:
        pass

    # 5. Urllib nativo
    try:
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            return response.read().decode("utf-8", errors="ignore")
    except Exception as e:
        pass

    return ""'''

# Reemplazar definicion
pattern = r'def fetch_tuazar_html\(\):.*?(?=def parse_tuazar_results_pure)'
match = re.search(pattern, text, re.DOTALL)
if match:
    new_text = text[:match.start()] + new_fetch_func + "\n\n\n" + text[match.end():]
    with open(server_path, "w", encoding="utf-8") as f:
        f.write(new_text)
    with open(r"C:\Users\victo\nuevas_ruletas\app_movil\static\server_zero_dep.py", "w", encoding="utf-8") as f:
        f.write(new_text)
    print("fetch_tuazar_html actualizado en server_zero_dep.py (ambas rutas)")
else:
    print("[-] No se pudo reemplazar fetch_tuazar_html")
