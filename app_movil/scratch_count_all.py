import sys
sys.path.append(r"C:\Users\victo\nuevas_ruletas\app_movil")
import server_zero_dep

live = server_zero_dep.parse_tuazar_results_pure()
counts = server_zero_dep.evaluate_and_update_all_pure(live)
print("Sorteos procesados por ruleta:", counts)

ops, stats = server_zero_dep.read_today_ledger()
print(f"\nTOTAL OPERACIONES LEÍDAS EN EL LEDGER DE HOY: {len(ops)}")
for i, o in enumerate(ops, 1):
    h = o.get("hora")
    r = o.get("ruleta")
    res = o.get("resultado")
    bet = o.get("total_bet")
    cand = o.get("candidatos")
    print(f"#{i:02d} | {h:<8} | {r:<25} | Jugados: {cand} | Salido: {res} | ${bet}")
