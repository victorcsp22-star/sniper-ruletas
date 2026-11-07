import urllib.request, json

data = json.loads(urllib.request.urlopen('http://127.0.0.1:5000/api/status').read().decode('utf-8'))
ledger = data.get('recent_ledger', [])
print("Ledger en el servidor local:")
hoy = [j for j in ledger if j.get('fecha') == '2026-11-02']
print(f"Total disparos hoy en servidor: {len(hoy)}")
for idx, j in enumerate(hoy, 1):
    cands = j.get('candidatos', '')
    salio = j.get('resultado', '')
    ruleta = j.get('ruleta', '')
    hora = j.get('hora', '')
    pnl = j.get('pnl', '')
    tipo = j.get('zona_patron', '')
    print(f"{idx:02d}. [{hora}] {ruleta} ({tipo}) -> Apostado: {cands} | Salio: {salio} | PnL: {pnl}")
