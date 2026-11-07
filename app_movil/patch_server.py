import re

p = r'C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py'
with open(p, 'r', encoding='utf-8') as f:
    content = f.read()

new_func = '''def fetch_tuazar_html():
    """Descarga el HTML de TuAzar con quintuple redundancia: PC Bridge, curl estatico local, curl de sistema, wget y urllib."""
    import subprocess
    import os

    # 1. PC Bridge (si la PC esta prendida en la red local)
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

    # 2. Curl Estatico Independiente (Binario musl aarch64 sin dependencias de OpenSSL de Android/Termux)
    for curl_candidate in ["./curl_static", "./static/curl_static", "/data/data/com.termux/files/home/sniper/curl_static"]:
        if os.path.exists(curl_candidate):
            try:
                res = subprocess.run(
                    [curl_candidate, "-k", "-s", "-L", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", url],
                    capture_output=True,
                    timeout=12
                )
                if res.returncode == 0 and len(res.stdout) > 2000:
                    print("[+] TuAzar descargado via curl_static 100% autonomo.")
                    return res.stdout.decode("utf-8", errors="ignore")
            except Exception as e:
                print(f"[-] curl_static fallo: {e}")

    # 3. Curl de sistema con bypass de certificados
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

    # 4. Wget nativo (no depende de OpenSSL de python)
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

    # 5. Urllib fallback
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

idx = content.find('def fetch_tuazar_html():')
idx2 = content.find('def parse_tuazar_results_pure()')
if idx != -1 and idx2 != -1:
    updated = content[:idx] + new_func + '\n\n\n' + content[idx2:]
    with open(p, 'w', encoding='utf-8') as f:
        f.write(updated)
    print("MODIFICADO EXITOSAMENTE")
else:
    print("NO SE ENCONTRARON LOS INDICES")
