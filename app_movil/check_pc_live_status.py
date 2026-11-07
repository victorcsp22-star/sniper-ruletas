import urllib.request, json

try:
    resp = urllib.request.urlopen('http://127.0.0.1:5000/api/status', timeout=3)
    data = json.loads(resp.read().decode('utf-8'))
    
    print("="*90)
    print("ESTADO EN VIVO DEL BOT EN LA PC (server_zero_dep.py)")
    print("="*90)
    print(f"Hora Servidor: {data.get('hora')} | Timestamp: {data.get('timestamp')}")
    w = data.get('wallet', {})
    print(f"Saldo en Mesa:        Bs {w.get('bankroll', 0.0):,.2f}")
    print(f"Operaciones Hoy:      {w.get('ops_today', 0)} disparos")
    print(f"Aciertos Hoy:         {w.get('wins_today', 0)} cobros")
    print(f"PnL del Dia:          Bs {w.get('pnl_today', 0.0):,.2f}")
    
    sigs = data.get('active_signals', [])
    print(f"\nDisparos Activos (COMPRAS INMINENTES): {len(sigs)}")
    if not sigs:
        print("  -> Sin compras para esta ronda (ruletas en espera disciplinada).")
    for s in sigs:
        cands = s.get('candidatos', [])
        cands_str = s.get('candidatos_str', '')
        fichas = len(cands)
        print(f"  [DISPARO ACTIVO] {s.get('ruleta')}:")
        print(f"     Animales ({fichas} fichas): {cands_str}")
        print(f"     Inversion: Bs {fichas*100:,.2f} (${fichas:.2f} USD) | Posible Premio: Bs {s.get('payout', 60)*100:,.2f} (${s.get('payout', 60):.2f} USD)")
        ultimo_clean = str(s.get('ultimo_salido', '')).encode('ascii', 'ignore').decode('ascii').strip()
        print(f"     Ultimo Salido: {ultimo_clean}")
        
    radars = data.get('radar_items', [])
    print(f"\nRADAR EN VIVO DE LAS 7 RULETAS MAESTRAS (8 LAGS):")
    print(f"{'RULETA':<18} | {'RACHA':<6} | {'ESTADO / GATILLO':<32} | {'ULTIMO SALIDO'}")
    print("-"*90)
    for r in radars:
        conteo_clean = r.get('conteo_str', '').encode('ascii', 'ignore').decode('ascii').strip()
        ultimo_clean = r.get('ultimo_salido', '').encode('ascii', 'ignore').decode('ascii').strip()
        print(f"{r.get('ruleta'):<18} | {r.get('racha'):<6} | {conteo_clean:<32} | {ultimo_clean}")
    print("="*90)
    
except Exception as e:
    print("Error consultando el servidor PC:", e)
