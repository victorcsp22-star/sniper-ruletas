import re

server_path = r"C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py"
static_path = r"C:\Users\victo\nuevas_ruletas\app_movil\static\server_zero_dep.py"

standalone_fetch_func = '''def fetch_tuazar_html():
    """Descarga el HTML de TuAzar de forma 100% autonoma desde el celular (Cero dependencia de PC)."""
    import subprocess
    import os

    url = "https://www.tuazar.com/loteria/animalitos/resultados/"

    # 1. Prioridad Absoluta: Curl Estatico Independiente Embebido (Binario musl aarch64 propio)
    curl_candidates = [
        "./curl_static",
        os.path.join(ROOT_DIR, "curl_static"),
        os.path.join(STATIC_DIR, "curl_static"),
        "/data/data/com.termux/files/home/sniper/curl_static",
        "./static/curl_static"
    ]
    for c_path in curl_candidates:
        if os.path.exists(c_path):
            try:
                try:
                    os.chmod(c_path, 0o777)
                except Exception:
                    pass
                res = subprocess.run(
                    [c_path, "-k", "-s", "-L", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", url],
                    capture_output=True,
                    timeout=10
                )
                if res.returncode == 0 and len(res.stdout) > 2000:
                    print("[+] TuAzar descargado via curl_static autónomo.")
                    return res.stdout.decode("utf-8", errors="ignore")
            except Exception:
                pass

    # 2. Wget Nativo de Android / Busybox (sin depender de OpenSSL de python)
    try:
        res = subprocess.run(
            ["wget", "--no-check-certificate", "-qO-", "--user-agent=Mozilla/5.0", url],
            capture_output=True,
            timeout=10
        )
        if res.returncode == 0 and len(res.stdout) > 2000:
            print("[+] TuAzar descargado via wget nativo.")
            return res.stdout.decode("utf-8", errors="ignore")
    except Exception:
        pass

    # 3. Curl del sistema con bypass
    try:
        res = subprocess.run(
            ["curl", "-k", "-s", "-L", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", url],
            capture_output=True,
            timeout=10
        )
        if res.returncode == 0 and len(res.stdout) > 2000:
            print("[+] TuAzar descargado via curl de sistema.")
            return res.stdout.decode("utf-8", errors="ignore")
    except Exception:
        pass

    # 4. Urllib nativo con contexto SSL permisivo
    try:
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            return response.read().decode("utf-8", errors="ignore")
    except Exception:
        pass

    # 5. Ultimo recurso: Si todo lo anterior falla y la PC estuviese encendida en la LAN
    for bridge_host in ["192.168.1.2:5000", "10.2.0.2:5000", "127.0.0.1:5000"]:
        try:
            pc_url = f"http://{bridge_host}/api/tuazar_bridge"
            with urllib.request.urlopen(pc_url, timeout=1) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                if len(html) > 2000:
                    print(f"[+] Fallback a PC Bridge ({bridge_host}).")
                    return html
        except Exception:
            pass

    return ""'''

for p in [server_path, static_path]:
    with open(p, "r", encoding="utf-8") as f:
        text = f.read()
    pattern = r'def fetch_tuazar_html\(\):.*?(?=def parse_tuazar_results_pure)'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        new_text = text[:match.start()] + standalone_fetch_func + "\n\n\n" + text[match.end():]
        with open(p, "w", encoding="utf-8") as f:
            f.write(new_text)
        print(f"[+] fetch_tuazar_html transformado a 100% AUTÓNOMO en {p}")
    else:
        print(f"[-] No se encontró patrón en {p}")
