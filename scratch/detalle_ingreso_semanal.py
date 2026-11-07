import sys
sys.path.append(r"C:\Users\victo\nuevas_ruletas\scratch")
from analizar_dias_semanas_perdidas import daily_plana, daily_pesos
import datetime, collections

def get_weekly_pnls(d_dict):
    semanas = collections.defaultdict(float)
    for d in sorted(d_dict.keys()):
        dt = datetime.datetime.strptime(d, "%Y-%m-%d").date()
        iso_year, iso_week, _ = dt.isocalendar()
        sem_key = f"{iso_year}-W{iso_week:02d}"
        p = d_dict[d]["cob"] - d_dict[d]["inv"]
        semanas[sem_key] += p
    return semanas

w_plana = get_weekly_pnls(daily_plana)
w_pesos = get_weekly_pnls(daily_pesos)

pnls_p = list(w_plana.values())
pnls_w = list(w_pesos.values())

# Solo semanas ganadoras
pos_p = [p for p in pnls_p if p > 0]
pos_w = [p for p in pnls_w if p > 0]

# Solo semanas perdedoras
neg_p = [p for p in pnls_p if p < 0]
neg_w = [p for p in pnls_w if p < 0]

print("=== DISTRIBUCIÓN REAL DE SEMANAS ===")
print("MODELO PLANO ($1.00 fijo):")
print(f"  Promedio neto global:            +${sum(pnls_p)/len(pnls_p):.2f} USD/semana")
print(f"  Promedio cuando la semana es GANADORA: +${sum(pos_p)/len(pos_p):.2f} USD")
print(f"  Promedio cuando la semana es PERDEDORA: -${abs(sum(neg_p)/len(neg_p)):.2f} USD")
print(f"  Mejor semana de la historia:     +${max(pnls_p):.2f} USD")
print()
print("SISTEMA DE PESOS (1 al 10):")
print(f"  Promedio neto global:            +${sum(pnls_w)/len(pnls_w):.2f} USD/semana")
print(f"  Promedio cuando la semana es GANADORA: +${sum(pos_w)/len(pos_w):.2f} USD")
print(f"  Promedio cuando la semana es PERDEDORA: -${abs(sum(neg_w)/len(neg_w)):.2f} USD")
print(f"  Mejor semana de la historia:     +${max(pnls_w):.2f} USD")
