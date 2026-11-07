import datetime, json, os, sys
sys.path.append(r"C:\Users\victo\nuevas_ruletas")
from bot_nuevas_ruletas import generate_upcoming_candidates, load_state, calculate_current_streak_and_misses
from config import RULETAS_CONFIG

now = datetime.datetime.now()
print("HORA ACTUAL:", now.strftime("%H:%M:%S"))

state = load_state()
print(f"Bankroll en state.json: {state.get('bankroll')}")

print("\n--- REVISIÓN DE LAS 9 RULETAS ---")
disparos_encontrados = []
for r_name, cfg in RULETAS_CONFIG.items():
    if not cfg.get("active", False):
        continue
    stk, mss = calculate_current_streak_and_misses(r_name)
    r_target = cfg.get("racha_target")
    is_target = stk == r_target
    print(f"{r_name:28} | Stk: {stk:2d} | Target: {r_target} | Disparo?: {is_target}")
    if is_target:
        cand = generate_upcoming_candidates(r_name)
        disparos_encontrados.append(cand)

print("\n--- CANDIDATOS ACTIVOS ---")
if disparos_encontrados:
    for d in disparos_encontrados:
        print(d)
else:
    print("NO HAY NINGÚN DISPARO ACTIVO EN ESTE PRECISO INSTANTE.")
