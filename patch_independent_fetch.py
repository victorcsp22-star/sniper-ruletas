import os

path_server = r"C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py"
with open(path_server, "r", encoding="utf-8") as f:
    text = f.read()

# Reemplazamos fetch_tuazar_html para que use wget de busybox de Android si curl y urllib fallan
# En Android, busybox wget descarga https usando TLS embebido del sistema o curl nativo
old_fetch = '''def fetch_tuazar_html():
    """Descarga el HTML de TuAzar con triple redundancia: Bridge PC (sin SSL), curl y urllib."""
    # Nivel 1: Si la PC esta encendida en la red local, obtener HTML directo por HTTP puro (Cero fallos SSL)
    pc_bridge_url = "http://192.168.1.2:5000/api/tuazar_bridge"
    try:
        with urllib.request.urlopen(pc_bridge_url, timeout=3) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            if len(html) > 2000:
                print("[+] HTML de TuAzar sincronizado via PC Bridge (100% estable).")
                return html
    except Exception:
        pass

    # Nivel 2: Conectar directamente a TuAzar por curl del sistema (si curl tiene certificados)
    url = "https://www.tuazar.com/loteria/animalitos/resultados/"
    try:
        import subprocess
        res = subprocess.run(
            ["curl", "-k", "-s", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", url],
            capture_output=True,
            timeout=10
        )
        if res.returncode == 0 and len(res.stdout) > 2000:
            print("[+] HTML descargado exitosamente via curl de sistema.")
            return res.stdout.decode("utf-8", errors="ignore")
    except Exception:
        pass

    # Nivel 3: Urllib nativo con contexto SSL permisivo
    try:
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            print("[+] HTML descargado exitosamente via urllib SSL permisivo.")
            return response.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"[-] Conexion directa fallo: {e}")

    return ""'''

new_fetch = '''def fetch_tuazar_html():
    """Descarga el HTML de TuAzar con cuadruple redundancia: PC Bridge, curl, busybox/wget y urllib."""
    # 1. PC Bridge (si la PC esta prendida en la red)
    try:
        pc_url = "http://192.168.1.2:5000/api/tuazar_bridge"
        with urllib.request.urlopen(pc_url, timeout=2) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            if len(html) > 2000:
                print("[+] TuAzar sincronizado via PC Bridge.")
                return html
    except Exception:
        pass

    url = "https://www.tuazar.com/loteria/animalitos/resultados/"
    import subprocess

    # 2. Curl con bypass de certificados
    try:
        res = subprocess.run(
            ["curl", "-k", "-s", "-L", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", url],
            capture_output=True,
            timeout=10
        )
        if res.returncode == 0 and len(res.stdout) > 2000:
            print("[+] TuAzar descargado via curl.")
            return res.stdout.decode("utf-8", errors="ignore")
    except Exception:
        pass

    # 3. Wget nativo (no depende de OpenSSL de python)
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

    # 4. Urllib fallback
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

text = text.replace(old_fetch, new_fetch)

with open(path_server, "w", encoding="utf-8") as f:
    f.write(text)

with open(r"C:\Users\victo\nuevas_ruletas\app_movil\static\server_zero_dep.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Servidor actualizado con wget/curl bypass independiente!")
