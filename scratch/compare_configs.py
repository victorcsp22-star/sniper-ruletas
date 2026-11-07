import sys, os
sys.path.append(r"C:\Users\victo\nuevas_ruletas")
from config import RULETAS_CONFIG

# Let's inspect server_zero_dep.py's RULETAS
import importlib.util
spec = importlib.util.spec_from_file_location("server_zero_dep", r"C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py")
server = importlib.util.module_from_spec(spec)
# we can read the file directly
with open(r"C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py", "r", encoding="utf-8") as f:
    text = f.read()

print("RULETAS_CONFIG en config.py:")
for r, cfg in RULETAS_CONFIG.items():
    if cfg.get("active", False):
        print(f"  {r:28}: markov={cfg.get('markov_snipers')} | mirror={cfg.get('mirror_pairs')} | lags={cfg.get('lags')}")

print("\nVerificando si markov_snipers o mirror_pairs están en server_zero_dep.py RULETAS...")
for r in RULETAS_CONFIG.keys():
    if r in text and "markov_snipers" in text:
        pass
