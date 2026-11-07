import os
import sys
import json
import pandas as pd
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = r"C:\Users\victo\nuevas_ruletas"
sys.path.append(ROOT_DIR)

from scratch.mine_markov_pairs_deep import RULETAS

with open(os.path.join(ROOT_DIR, "scratch", "markov_selective_memory_pairs.json"), "r", encoding="utf-8") as f:
    data = json.load(f)

print("PAR DE TRANSICIONES CERTIFICADAS CON MEMORIA SELECTIVA VIGENTE:")
print("=" * 80)

selected_config = {}

for r_name, r_info in data.items():
    pairs = r_info["top_pairs"]
    # Filtro de memoria selectiva: Z >= 3.00, EV > +60%, y ACTIVO RECIENTEMENTE (🟢 VIGENTE)
    filtered = [p for p in pairs if p["z_score"] >= 3.0 and p["is_active_recently"] and p["ev_pct"] >= 60.0]
    
    mapping = {}
    print(f"\n{r_name}:")
    for p in filtered:
        from_n = p["from_num"]
        to_n = p["to_num"]
        # Tomar el de mayor Z si hay colisiones
        if from_n not in mapping:
            mapping[from_n] = to_n
            print(f"  • #{from_n} {p['from_animal']} -> #{to_n} {p['to_animal']} | Prob: {p['prob']}% (Lift {p['lift']}x) | Z: +{p['z_score']} | EV: +{p['ev_pct']}% | Reciente: {p['recent_count']} aciertos")
    
    selected_config[r_name] = mapping

print("\n" + "=" * 80)
print("Configuración generada para el bot:")
print(json.dumps(selected_config, indent=2, ensure_ascii=False))
