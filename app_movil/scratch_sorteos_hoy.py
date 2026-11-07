import sys; sys.path.append(r"C:\Users\victo\nuevas_ruletas\app_movil")
import server_zero_dep

res = server_zero_dep.parse_tuazar_results_pure()
for r, draws in res.items():
    print(f"=== {r} ({len(draws)} sorteos hoy) ===")
    for d in draws:
        print(f"  {d['hora']:<9} -> #{d['numero']} {d['animal']}")
