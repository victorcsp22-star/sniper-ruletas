import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(r"C:\Users\victo\nuevas_ruletas")
from config import RULETAS_CONFIG
sys.path.append(r"C:\Users\victo\nuevas_ruletas\app_movil")
import server_zero_dep

# Update server_zero_dep.RULETAS with config.RULETAS_CONFIG
for r_name, cfg in RULETAS_CONFIG.items():
    if r_name in server_zero_dep.RULETAS:
        server_zero_dep.RULETAS[r_name]["markov_snipers"] = cfg.get("markov_snipers", {})
        server_zero_dep.RULETAS[r_name]["mirror_pairs"] = cfg.get("mirror_pairs", {})

print("Probando get_current_streaks después de actualizar RULETAS:")
for r_name in server_zero_dep.RULETAS.keys():
    stk, miss, info = server_zero_dep.get_current_streaks(r_name)
    if info.get("is_markov"):
        print(f"🚨 ALERTA MARKOV DETECTADA EN {r_name}: {info.get('cands')}")
