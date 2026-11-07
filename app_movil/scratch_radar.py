import sys; sys.path.append(r"C:\Users\victo\nuevas_ruletas")
from bot_nuevas_ruletas import check_and_update

res = check_and_update(verbose=False)
print("TOTAL SENALES ACTIVAS:", len(res["active_signals"]))
for a in res["active_signals"]:
    print("SEÑAL ACTIVA:", a["ruleta"], a["candidates_str"], a["total_stake"])

print("\n--- RADAR COMPLETO ---")
for item in res["radar_items"]:
    print(item["ruleta"], "| Racha:", item["racha"], "| Estado:", item["conteo_str"], "| Faltan:", item["fallos_restantes"])
