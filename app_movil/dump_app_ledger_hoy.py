import urllib.request, json

# Consultar el ledger real que tiene la app en el celular
data = json.loads(urllib.request.urlopen('http://192.168.1.7:5000/api/status').read().decode('utf-8'))
ledger = data.get('recent_ledger', [])
print(f"Total filas en ledger del celular: {len(ledger)}")

# Filtrar sólo las de hoy (2026-11-02)
hoy_ops = [j for j in ledger if j.get('fecha') == '2026-11-02']
print(f"Total disparos mostrados en la app hoy (2026-11-02): {len(hoy_ops)}")

for idx, j in enumerate(hoy_ops, 1):
    cands = j.get('candidatos', '')
    salio = j.get('resultado', '')
    ruleta = j.get('ruleta', '')
    hora = j.get('hora', '')
    pnl = j.get('pnl', '')
    tipo = j.get('zona_patron', '')
    print(f"{idx:02d}. [{hora}] {ruleta} ({tipo})")
    print(f"     Apostado: {cands}")
    print(f"     Salio: {salio} | PnL: {pnl}")
