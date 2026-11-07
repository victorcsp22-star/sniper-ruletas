import urllib.request, json

data = json.loads(urllib.request.urlopen('http://192.168.1.7:5000/api/status').read().decode('utf-8'))
print("=== ESTADO DEL RADAR EN EL CELULAR (15:23) ===")
print("Senales activas para proximo sorteo:", data.get('active_signals'))
print("\nItems del radar:")
for r in data.get('radar_items', []):
    print(f"- {r.get('ruleta')}: racha={r.get('racha')} misses={r.get('misses')} badge={r.get('badge')} ultimo={r.get('ultimo_salido')}")
