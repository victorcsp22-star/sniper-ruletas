import urllib.request, json

data = json.loads(urllib.request.urlopen('http://192.168.1.7:5000/api/status').read().decode('utf-8'))
print("=== ESTADO EN VIVO CELULAR (16:18) ===")
print("Wallet:", data.get('wallet'))
print("\nSenales activas:")
for s in data.get('active_signals', []):
    txt = f"ALERTA: {s.get('ruleta')} | Tipo: {s.get('tipo')} | Fichas: {s.get('total_fichas')} | Candidatos: {s.get('candidatos_str')}"
    print(txt.encode('ascii', errors='ignore').decode())

print("\nUltimas 3 jugadas registradas en el ledger:")
for j in data.get('recent_ledger', [])[-3:]:
    txt = f"[{j.get('fecha')} {j.get('hora')}] {j.get('ruleta')} -> {j.get('candidatos')} | Salio: {j.get('resultado')} | Cond: {j.get('condicion')} | PnL: {j.get('pnl')}"
    print(txt.encode('ascii', errors='ignore').decode())
