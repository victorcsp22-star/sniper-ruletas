import urllib.request, json

data = json.loads(urllib.request.urlopen('http://192.168.1.7:5000/api/status').read().decode('utf-8'))
print("=== JUGADAS EXCLUSIVAS DE HOY (2026-11-02) EN EL CELULAR ===")
ops_hoy = [j for j in data.get('recent_ledger', []) if j.get('fecha') == '2026-11-02']
print(f"Total disparos ejecutados hoy: {len(ops_hoy)}")
for j in ops_hoy:
    print(f"[{j.get('hora')}] {j.get('ruleta')} | Apostado: {j.get('candidatos')} | Salio: {j.get('resultado')} | Perdida: Bs {j.get('pnl')}")
