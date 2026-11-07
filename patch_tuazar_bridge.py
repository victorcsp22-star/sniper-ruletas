import os

path_server = r"C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py"
with open(path_server, "r", encoding="utf-8") as f:
    text = f.read()

# Reemplazamos fetch_tuazar_html para que tenga 3 niveles de conexion:
# 1. Conectar a TuAzar via PC local (http://192.168.1.2:5000/api/tuazar_html) -> 100% libre de errores SSL en Android
# 2. Conectar via curl de sistema
# 3. Conectar via urllib nativo

old_func = '''def fetch_tuazar_html():
    """Descarga el HTML de TuAzar soportando curl de sistema (indispensable en Termux sin SSL) y urllib."""
    url = "https://www.tuazar.com/loteria/animalitos/resultados/"
    # 1. Intentar con curl del sistema (funciona 100% en Termux aunque Python no tenga módulo _ssl)
    try:
        import subprocess
        res = subprocess.run(
            ["curl", "-k", "-s", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", url],
            capture_output=True,
            timeout=12
        )
        if res.returncode == 0 and len(res.stdout) > 2000:
            print("[+] HTML descargado exitosamente vía curl de sistema.")
            return res.stdout.decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"[*] curl no disponible ({e}). Intentando urllib...")

    # 2. Intentar con urllib nativo
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=12) as response:
            print("[+] HTML descargado exitosamente vía urllib.")
            return response.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"[-] urllib falló ({e}).")

    return ""'''

new_func = '''def fetch_tuazar_html():
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

# Anadir endpoint /api/tuazar_bridge en do_GET de SniperHandler
old_get = '''    def do_GET(self):
        if self.path == "/api/status":
            self.handle_api_status()
        elif self.path == "/api/reporte":
            self.handle_api_reporte()'''

new_get = '''    def do_GET(self):
        if self.path == "/api/status":
            self.handle_api_status()
        elif self.path == "/api/reporte":
            self.handle_api_reporte()
        elif self.path == "/api/tuazar_bridge":
            # Sirve el HTML fresco de TuAzar al celular por HTTP puro
            url = "https://www.tuazar.com/loteria/animalitos/resultados/"
            try:
                import subprocess
                res = subprocess.run(["curl.exe", "-k", "-s", "-A", "Mozilla/5.0", url], capture_output=True, timeout=10)
                html_bytes = res.stdout if len(res.stdout) > 2000 else b""
                if not html_bytes:
                    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=10) as r:
                        html_bytes = r.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html_bytes)))
                self.end_headers()
                self.wfile.write(html_bytes)
            except Exception as e:
                self.send_error(500, str(e))'''

text = text.replace(old_func, new_func)
text = text.replace(old_get, new_get)

with open(path_server, "w", encoding="utf-8") as f:
    f.write(text)

with open(r"C:\Users\victo\nuevas_ruletas\app_movil\static\server_zero_dep.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Servidor blindado con Triple Redundancia (Bridge PC + curl + ssl unverified)!")
