import urllib.request, json

data = json.loads(urllib.request.urlopen('http://192.168.1.7:5000/api/status').read().decode('utf-8'))
print("=== TODAS LAS JUGADAS DEL CELULAR ===")
for j in data.get('recent_ledger', []):
    txt = f"[{j.get('fecha')} {j.get('hora')}] {j.get('ruleta')} | Apostado: {j.get('candidatos')} | Salio: {j.get('resultado')} | PnL: {j.get('pnl')}"
    print(txt.encode('ascii', errors='ignore').decode())
