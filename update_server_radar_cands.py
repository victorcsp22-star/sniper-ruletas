import os

path = "C:/Users/victo/nuevas_ruletas/app_movil/server_zero_dep.py"
with open(path, "r", encoding="utf-8") as f:
    c = f.read()

target = """                radar_items.append({
                    "ruleta": r_name,
                    "emoji": cfg["emoji"],
                    "payout": cfg["payout"],
                    "racha": stk,
                    "misses": miss,
                    "badge": badge,
                    "conteo_str": conteo,
                    "urgencia": urg,
                    "peso_agente": p_agente,
                    "peso_label": p_label,
                    "ultimo_salido": info.get("last_str", "---"),
                    "is_markov": False,
                    "is_anti_blocked": is_anti,
                    "burbuja": burbuja
                })"""

replacement = """                c_str = ""
                if urg == 1:
                    if r_name in state.get("pending_bets", {}):
                        c_str = state["pending_bets"][r_name].get("candidatos_str", "")
                    elif cands:
                        c_str = ", ".join([f"#{c['numero']} {c['animal']} [{p_label}]" for c in cands])

                radar_items.append({
                    "ruleta": r_name,
                    "emoji": cfg["emoji"],
                    "payout": cfg["payout"],
                    "racha": stk,
                    "misses": miss,
                    "badge": badge,
                    "conteo_str": conteo,
                    "urgencia": urg,
                    "peso_agente": p_agente,
                    "peso_label": p_label,
                    "ultimo_salido": info.get("last_str", "---"),
                    "is_markov": False,
                    "is_anti_blocked": is_anti,
                    "burbuja": burbuja,
                    "candidatos_str": c_str
                })"""

c_norm = c.replace("\r\n", "\n")
t_norm = target.replace("\r\n", "\n")
r_norm = replacement.replace("\r\n", "\n")

if t_norm in c_norm:
    c_norm = c_norm.replace(t_norm, r_norm, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(c_norm)
    print("Updated server_zero_dep.py radar_items.")
else:
    print("Could not find target in server_zero_dep.py.")
