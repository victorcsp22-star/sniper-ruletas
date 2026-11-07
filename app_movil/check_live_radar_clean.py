import urllib.request, json

data = json.loads(urllib.request.urlopen('http://192.168.1.7:5000/api/status').read().decode('utf-8'))
print("=== ESTADO DEL RADAR EN EL CELULAR (15:23) ===")
for s in data.get('active_signals', []):
    print(f"ALERTA: {s.get('ruleta')} | Tipo: {s.get('tipo')} | Fichas: {s.get('total_fichas')} | Candidatos: {s.get('candidatos_str')}")

print("\nRuletas en observacion:")
for r in data.get('radar_items', []):
    badge = r.get('badge', '').encode('ascii', errors='ignore').decode()
    print(f"- {r.get('ruleta')}: racha={r.get('racha')} misses={r.get('misses')} badge={badge} ultimo={r.get('ultimo_salido')}")
