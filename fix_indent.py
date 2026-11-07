import os

path = r"C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py"
with open(path, "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

bad_block = """        # 2. Windows PC (curl.exe nativo)
        # 2. curl en PATH (Windows o Termux)
        curl_cmd = "curl.exe" if sys.platform == "win32" else "curl"
            try:
                res = subprocess.run(
                    [curl_cmd, "-k", "-s", "-L", "--connect-timeout", "6", "-m", "10", "-A", ua, url],
                    capture_output=True,
                    timeout=12
                )
                if res.returncode == 0 and len(res.stdout) > 2000:
                    return res.stdout.decode("utf-8", errors="ignore")
            except Exception:
                pass"""

good_block = """        # 2. curl en PATH del sistema (Windows o Termux/Linux)
        curl_cmd = "curl.exe" if sys.platform == "win32" else "curl"
        try:
            res = subprocess.run(
                [curl_cmd, "-k", "-s", "-L", "--connect-timeout", "6", "-m", "10", "-A", ua, url],
                capture_output=True,
                timeout=12
            )
            if res.returncode == 0 and len(res.stdout) > 2000:
                return res.stdout.decode("utf-8", errors="ignore")
        except Exception:
            pass"""

text = text.replace(bad_block, good_block)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Indentacion corregida.")
