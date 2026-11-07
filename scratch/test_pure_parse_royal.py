import sys
sys.path.append(r'C:\Users\victo\nuevas_ruletas\app_movil')
from server_zero_dep import parse_tuazar_results_pure

res = parse_tuazar_results_pure()
print("Ruleta Royal results from parse_tuazar_results_pure():")
for r in res.get("Ruleta Royal", []):
    print(" ", r)
