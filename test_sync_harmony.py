import urllib.request, json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

# 1. State from file (used by bot_nuevas_ruletas.py)
with open(r'C:\Users\victo\nuevas_ruletas\state_nuevas_ruletas.json', 'r', encoding='utf-8') as f:
    state_pc = json.load(f)

# 2. State from Mobile App API (server_zero_dep.py)
with urllib.request.urlopen('http://localhost:5000/api/status') as r:
    api_app = json.loads(r.read().decode('utf-8'))

print("=== 1. COMPARATIVA DE WALLET / SALDOS ===")
bank_pc = state_pc.get("bankroll", 0)
with_pc = state_pc.get("total_withdrawn", 0)
print(f"PC Bot State -> Mesa: ${bank_pc:.2f} USD | Retirado: ${with_pc:.2f} USD | Patrimonio: ${bank_pc+with_pc:.2f} USD")
print(f"App Móvil    -> Mesa: ${api_app['wallet']['bankroll']:.2f} USD | Retirado: ${api_app['wallet']['withdrawn']:.2f} USD | Patrimonio: ${api_app['wallet']['patrimonio']:.2f} USD")
if abs(bank_pc - api_app['wallet']['bankroll']) < 0.01 and abs(with_pc - api_app['wallet']['withdrawn']) < 0.01:
    print("✅ SALDOS: 100% EN PERFECTA ARMONÍA")
else:
    print("⚠️ DISCREPANCIA EN SALDOS DETECTADA")

print("\n=== 2. COMPARATIVA DE RACHAS EN EL RADAR ===")
app_radar_map = {it['ruleta']: it for it in api_app['radar_items']}
all_matched = True
for r_name, r_streak in state_pc.get('streaks', {}).items():
    if r_name in app_radar_map:
        it = app_radar_map[r_name]
        b = it.get('burbuja', {})
        match = (r_streak == it['racha'])
        if not match:
            all_matched = False
        status_ico = "✅" if match else "❌"
        print(f"{status_ico} {r_name:<28} | PC Racha: {r_streak:>2} | App Racha: {it['racha']:>2} | Burbuja: {b.get('badge')} | Estado: {it['conteo_str']}")

if all_matched:
    print("✅ RACHAS Y BURBUJAS: 100% EN PERFECTA ARMONÍA")

print("\n=== 3. COMPARATIVA DE SEÑALES ACTIVAS INMINENTES ===")
pc_pending = state_pc.get('pending_bets', {})
app_signals = api_app.get('active_signals', [])
print(f"Total Señales -> PC: {len(pc_pending)} | App Móvil: {len(app_signals)}")

for r_name, p in pc_pending.items():
    cands_pc = p.get('candidatos', [])
    stake_pc = p.get('stake_unit', 0)
    total_pc = p.get('total_stake', 0)
    
    # Buscar en app
    app_sig = next((s for s in app_signals if s.get('ruleta') == r_name), None)
    if app_sig:
        cands_app = app_sig.get('candidatos', [])
        # Puede venir como lista de dicts o lista de strings
        if cands_app and isinstance(cands_app[0], dict):
            cands_app = [str(c['numero']) for c in cands_app]
        else:
            cands_app = [str(c) for c in cands_app]
        
        stake_app = app_sig.get('stake_unit', 0)
        total_app = app_sig.get('costo', 0)
        
        cands_match = (set(cands_pc) == set(cands_app))
        stake_match = (abs(stake_pc - stake_app) < 0.01)
        total_match = (abs(total_pc - total_app) < 0.01)
        
        print(f"\n🎯 RULETA: {r_name}")
        print(f"   • Animales PC : {cands_pc}")
        print(f"   • Animales App: {cands_app} -> {'✅ COINCIDEN' if cands_match else '❌ DISCREPAN'}")
        print(f"   • Monto c/u PC : ${stake_pc:.2f} USD | App: ${stake_app:.2f} USD -> {'✅ COINCIDEN' if stake_match else '❌ DISCREPAN'}")
        print(f"   • Costo Total PC: ${total_pc:.2f} USD | App: ${total_app:.2f} USD -> {'✅ COINCIDEN' if total_match else '❌ DISCREPAN'}")
    else:
        print(f"❌ Ruleta {r_name} activa en PC pero ausente en App")
