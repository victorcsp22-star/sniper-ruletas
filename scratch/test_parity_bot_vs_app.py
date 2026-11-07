import sys
sys.path.append(r'C:\Users\victo\nuevas_ruletas')
sys.path.append(r'C:\Users\victo\nuevas_ruletas\app_movil')

from bot_nuevas_ruletas import calculate_current_streak_and_misses, generate_upcoming_candidates
from server_zero_dep import get_current_streaks as streaks_mobile
from config import RULETAS_CONFIG

print("="*75)
print("AUDITORÍA DE PARIDAD: MOTOR BOT (PC) vs APLICACIÓN MÓVIL (CELULAR)")
print("="*75)

all_match = True
for r in RULETAS_CONFIG:
    if not RULETAS_CONFIG[r].get("active", False):
        continue
    stk_b, miss_b = calculate_current_streak_and_misses(r)
    cands_b_info = generate_upcoming_candidates(r)
    c_b = [f"#{c['numero']} {c['animal']}" for c in cands_b_info.get("candidates", [])]
    
    stk_m, miss_m, info_m = streaks_mobile(r)
    c_m = [f"#{c['numero']} {c['animal']}" for c in info_m.get("cands", [])]
    
    match_streak = (stk_b == stk_m)
    match_cands = (c_b == c_m)
    
    status = "100% EXACTO" if (match_streak and match_cands) else "DISCREPANCIA"
    if not (match_streak and match_cands):
        all_match = False
        
    print(f"Ruleta: {r}")
    print(f"  • Bot PC    : Racha={stk_b} | Candidatos={c_b}")
    print(f"  • App Móvil : Racha={stk_m} | Candidatos={c_m}")
    print(f"  • Resultado : {status}\n")

print("="*75)
print(f"VEREDICTO FINAL DE REPLICACIÓN: {'PARIDAD ABSOLUTA (100% IDÉNTICOS)' if all_match else 'FALLO DE SINCRONIZACIÓN'}")
print("="*75)
