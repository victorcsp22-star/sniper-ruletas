import sys
sys.path.append(r"C:\Users\victo\nuevas_ruletas\app_movil")
import server_zero_dep
sys.path.append(r"C:\Users\victo\nuevas_ruletas")
import bot_nuevas_ruletas

print("COMPARATIVA DE CANDIDATOS ENTRE BOT PC Y SERVER MÓVIL:")
discrepancias = 0
for r in bot_nuevas_ruletas.RULETAS_CONFIG:
    if not bot_nuevas_ruletas.RULETAS_CONFIG[r].get("active"): continue
    c_bot = bot_nuevas_ruletas.generate_upcoming_candidates(r)
    s_szd, m_szd, info_szd = server_zero_dep.get_current_streaks(r)
    nums_bot = [c["numero"] for c in c_bot["candidates"]]
    nums_szd = [c["numero"] for c in info_szd["cands"]]
    is_m_bot = c_bot["is_markov_active"]
    is_m_szd = info_szd["is_markov"]
    
    diff = (nums_bot != nums_szd or is_m_bot != is_m_szd)
    if diff:
        discrepancias += 1
    status = "IDENTICO" if not diff else "DISCREPANCIA"
    print(f"[{status}] {r:28} | Bot={nums_bot} (Markov={is_m_bot}) | Movil={nums_szd} (Markov={is_m_szd})")

print(f"\nTOTAL DISCREPANCIAS EN CANDIDATOS: {discrepancias}")
