import os, sys

path = r"C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py"
with open(path, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if '"/data/data/com.termux/files/home/sniper/curl_static",' in line:
        new_lines.append('        "/data/data/com.termux/files/usr/bin/curl",\n')
    
    if 'if os.path.exists(cp) and os.path.getsize(cp) > 1000000:' in line:
        line = '        if os.path.exists(cp) and (os.path.getsize(cp) > 1000000 or "usr/bin/curl" in cp):\n'
    
    if 'if sys.platform == "win32":' in line:
        new_lines.append('        # 2. curl en PATH (Windows o Termux)\n')
        new_lines.append('        curl_cmd = "curl.exe" if sys.platform == "win32" else "curl"\n')
        continue
    
    if '["curl.exe", "-k", "-s", "-L"' in line:
        line = line.replace('"curl.exe"', 'curl_cmd')

    new_lines.append(line)

with open(path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Patch aplicado con éxito.")
