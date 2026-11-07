import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(r'C:\Users\victo\nuevas_ruletas')
sys.path.append(r'C:\Users\victo\nuevas_ruletas\app_movil')

from server_zero_dep import get_current_streaks, RULETAS

print("="*80)
print("REVISIÓN DE SEÑALES LISTAS PARA MAÑANA TEMPRANO")
print("="*80)

active_list = []
waiting_list = []

for r_name, cfg in RULETAS.items():
    stk, miss, info = get_current_streaks(r_name)
    cands = info.get("cands", [])
    cands_str = ", ".join([f"#{c['numero']} {c['animal']}" for c in cands])
    is_markov = info.get("is_markov", False)
    is_anti = info.get("is_anti_blocked", False)
    target = [1, 2] if r_name == "Gatazo" else [1]
    
    is_trigger = ((stk in target) and not is_anti) or is_markov
    last_str = info.get("last_str", "---")
    
    item = {
        "ruleta": r_name,
        "emoji": cfg["emoji"],
        "racha": stk,
        "payout": cfg["payout"],
        "is_trigger": is_trigger,
        "is_markov": is_markov,
        "cands_count": len(cands),
        "cands_str": cands_str,
        "last_salido": last_str
    }
    
    if is_trigger:
        active_list.append(item)
    else:
        waiting_list.append(item)

print("\n🚨 1. RULETAS CON DISPARO ACTIVO LISTAS PARA MAÑANA:")
if active_list:
    for a in active_list:
        print(f"  {a['emoji']} {a['ruleta']}:")
        print(f"     • Condición: {'⚡ Gatillo Markov' if a['is_markov'] else f'🔥 Racha {a['racha']} (Objetivo)'}")
        print(f"     • Último Salido Hoy: {a['last_salido']}")
        print(f"     • ANIMALITOS A JUGAR: {a['cands_str']}")
        print(f"     • Fichas a Apostar: {a['cands_count']} fichas de $1.00 USD (Total: ${a['cands_count']:.2f} USD)")
        print(f"     • Premio Potencial: ${a['payout']:.2f} USD\n")
else:
    print("  (Ninguna ruleta activa)")

print("💤 2. RULETAS EN ESPERA / OBSERVACIÓN (SIN DISPARO MAÑANA TEMPRANO):")
for w in waiting_list:
    print(f"  {w['emoji']} {w['ruleta']:18} | Racha actual: {w['racha']:2d} | Último: {w['last_salido']}")
print("="*80)
