import urllib.request, json

data = json.loads(urllib.request.urlopen('http://192.168.1.7:5000/api/status').read().decode('utf-8'))
ledger = data.get('recent_ledger', [])
print("DETALLE COMPLETO DE LOS FALLOS CONSECUTIVOS:")
total_perdido = 0
total_fichas = 0
for idx, j in enumerate(ledger, 1):
    pnl = float(j.get('pnl', 0.0))
    total_perdido += abs(pnl)
    cands = str(j.get('candidatos', '')).split(',')
    fichas = len(cands)
    total_fichas += fichas
    print(f"{idx:02d}. [{j.get('fecha')} {j.get('hora')}] {j.get('ruleta')}")
    print(f"    Apostado ({fichas} fichas): {j.get('candidatos')}")
    print(f"    Salio: {j.get('resultado')} | Perdida: Bs {abs(pnl):,.2f}")

print("\n--- RESUMEN EXACTO ---")
print(f"Racha de fallos consecutivos: {len(ledger)}")
print(f"Total fichas jugadas (a Bs 100 c/u): {total_fichas}")
print(f"Capital total absorbido: Bs {total_perdido:,.2f}")
print(f"Balance inicial: Bs 20,000.00")
print(f"Balance restante en mesa: Bs {20000.0 - total_perdido:,.2f}")
print(f"Drawdown actual: -{(total_perdido / 20000.0)*100:.2f}%")
