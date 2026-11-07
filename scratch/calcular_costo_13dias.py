import sys
sys.path.append(r"C:\Users\victo\nuevas_ruletas\scratch")
from analizar_dias_semanas_perdidas import daily_plana, daily_pesos
import datetime

def aislar_peor_racha_dias(d_dict, nombre):
    days = sorted(d_dict.keys())
    pnls = [d_dict[d]["cob"] - d_dict[d]["inv"] for d in days]
    invs = [d_dict[d]["inv"] for d in days]
    cobs = [d_dict[d]["cob"] for d in days]
    ops = [d_dict[d]["ops"] for d in days]
    
    # Encontrar la racha más larga de días perdedores (pnl < 0)
    max_streak = 0
    cur_streak = 0
    start_idx = 0
    best_start = 0
    best_end = 0
    
    for i, p in enumerate(pnls):
        if p < 0:
            if cur_streak == 0:
                start_idx = i
            cur_streak += 1
            if cur_streak > max_streak:
                max_streak = cur_streak
                best_start = start_idx
                best_end = i
        else:
            cur_streak = 0
            
    # Calcular métricas acumuladas de esa racha de 13 días
    streak_days = days[best_start:best_end+1]
    streak_pnls = pnls[best_start:best_end+1]
    streak_invs = invs[best_start:best_end+1]
    streak_cobs = cobs[best_start:best_end+1]
    streak_ops = ops[best_start:best_end+1]
    
    total_perdida = sum(streak_pnls)
    total_invertido = sum(streak_invs)
    total_cobrado = sum(streak_cobs)
    total_disparos = sum(streak_ops)
    
    print(f"=== {nombre} ===")
    print(f"Duración: {len(streak_days)} días consecutivos en rojo")
    print(f"Período exacto: Desde {streak_days[0]} hasta {streak_days[-1]}")
    print(f"Disparos ejecutados en esos 13 días: {total_disparos} disparos")
    print(f"Total Invertido en la racha:  ${total_invertido:,.2f} USD")
    print(f"Total Cobrado en la racha:    ${total_cobrado:,.2f} USD")
    print(f"PÉRDIDA NETA ACUMULADA:       ${total_perdida:,.2f} USD")
    print()
    print("Detalle día a día de la racha:")
    for d, p, inv, cob, op in zip(streak_days, streak_pnls, streak_invs, streak_cobs, streak_ops):
        print(f"  {d}: {op:>2} disparos | Inv: ${inv:>5.2f} | Cob: ${cob:>5.2f} | PnL: ${p:>+6.2f} USD")
    print("-" * 65)

aislar_peor_racha_dias(daily_plana, "INVERSIÓN PLANA ($1.00 FIJO)")
aislar_peor_racha_dias(daily_pesos, "SISTEMA DE PESOS (1 AL 10)")
