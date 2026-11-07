import urllib.request, zipfile, io, re

resp = urllib.request.urlopen('http://192.168.1.2:5000/static/sniper_ruletas.zip')
z = zipfile.ZipFile(io.BytesIO(resp.read()))

code1 = z.read('server_zero_dep.py').decode('utf-8', errors='ignore')
matches1 = re.findall(r'"title":\s*"(.*?)"', code1)
print(f"Ruletas en server_zero_dep.py del zip: {len(matches1)}")
for m in matches1:
    print(f"  * {m}")

code2 = z.read('static/server_zero_dep.py').decode('utf-8', errors='ignore')
matches2 = re.findall(r'"title":\s*"(.*?)"', code2)
print(f"Ruletas en static/server_zero_dep.py del zip: {len(matches2)}")
for m in matches2:
    print(f"  * {m}")
