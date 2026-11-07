"""
Auditoría Forense de Días y Semanas Perdedoras en la Cartera Élite de 9 Ruletas.
Analiza sorteo a sorteo sobre los 2 años completos (6,832 disparos):
1. PnL diario consolidado de toda la cartera.
2. Días ganadores vs días perdedores vs días neutros.
3. Racha máxima y promedio de DÍAS consecutivos en pérdida.
4. PnL semanal consolidado (ciclos de lunes a domingo o bloques de 7 días).
5. Semanas ganadoras vs semanas perdedoras.
6. Racha máxima y promedio de SEMANAS consecutivas en pérdida.
7. Distribución de caídas (Drawdowns) y recuperación de la banca.
"""

import os, collections, datetime, json
import pandas as pd
import numpy as np

OUTPUT_DIR = r"C:\Users\victo\nuevas_ruletas"

CONFIG_9 = {
    "Lotto Gato": {
        "file": os.path.join(OUTPUT_DIR, "lotto_gato.csv"),
        "payout": 60.0, "lags": [18, 38, 14], "rec_w": 6,
        "target_streaks": [1, 2], "wr_optimos": [1, 2],
        "markov": {"14": "0", "27": "15", "3": "7"}
    },
    "Granja Mill. Granjazo": {
        "file": os.path.join(OUTPUT_DIR, "granja_millonaria_granjazo.csv"),
        "payout": 60.0, "lags": [45, 26, 15], "rec_w": 6,
        "target_streaks": [1, 3], "wr_optimos": [1, 3],
        "markov": {}
    },
    "Loto Chaima": {
        "file": os.path.join(OUTPUT_DIR, "loto_chaima.csv"),
        "payout": 60.0, "lags": [49, 41, 35], "rec_w": 6,
        "target_streaks": [0, 1], "wr_optimos": [0, 1],
        "markov": {"48": "0", "55": "0", "12": "0"}
    },
    "Guacharo Activo": {
        "file": os.path.join(OUTPUT_DIR, "data_vz", "guacharo_activo_2anios.csv"),
        "payout": 60.0, "lags": [31, 54, 41], "rec_w": 8,
        "target_streaks": [1, 3], "wr_optimos": [1, 3, 6],
        "markov": {"21": "0", "8": "67", "29": "2"}
    },
    "Mega Animal 40": {
        "file": os.path.join(OUTPUT_DIR, "mega_animal_40.csv"),
        "payout": 30.0, "lags": [18, 20, 43], "rec_w": 8,
        "target_streaks": [1, 2, 3], "wr_optimos": [0, 1, 2, 3],
        "markov": {"30": "0", "11": "0", "32": "35"}
    },
    "Ruleta Royal": {
        "file": os.path.join(OUTPUT_DIR, "data_vz", "ruleta_royal_2anios.csv"),
        "payout": 30.0, "lags": [19, 16, 31], "rec_w": 6,
        "target_streaks": [1], "wr_optimos": [0, 1, 6],
        "markov": {"25": "22", "8": "27"}
    },
    "Lotto Activo": {
        "file": os.path.join(OUTPUT_DIR, "data_vz", "lotto_activo_2anios.csv"),
        "payout": 30.0, "lags": [20, 18, 15], "rec_w": 6,
        "target_streaks": [1, 2], "wr_optimos": [0, 1, 2],
        "markov": {"14": "0", "31": "0", "6": "0"}
    },
    "Gatazo": {
        "file": os.path.join(OUTPUT_DIR, "gatazo.csv"),
        "payout": 60.0, "lags": [35, 9, 20], "rec_w": 6,
        "target_streaks": [1], "wr_optimos": [1, 11, 12],
        "markov": {"30": "63", "48": "21", "23": "42"}
    },
    "Monje Millonario": {
        "file": os.path.join(OUTPUT_DIR, "monje_millonario.csv"),
        "payout": 60.0, "lags": [24, 42, 48], "rec_w": 6,
        "target_streaks": [0, 1], "wr_optimos": [0, 1],
        "markov": {}
    }
}

def calcular_peso_agente(r_name, streak, trigger_miss, payout, cfg):
    wr_optimos = cfg["wr_optimos"]
    s_racha = 4 if streak in wr_optimos else (3 if streak <= 1 else (2 if streak <= 5 else (1 if streak <= 20 else 0)))
    s_pago = 3 if payout >= 60.0 else 2
    s_trigger = 3 if 1 <= trigger_miss <= 3 else (1 if trigger_miss == 0 else (2 if trigger_miss <= 8 else 0))
    return max(1, min(10, s_racha + s_pago + s_trigger))

all_events = []
for r_name, cfg in CONFIG_9.items():
    if not os.path.exists(cfg["file"]): continue
    df = pd.read_csv(cfg["file"])
    df["dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], errors="coerce")
    df = df.dropna(subset=["dt", "numero"]).sort_values(by="dt").reset_index(drop=True)
    
    nums = [str(x).strip() for x in df["numero"].tolist()]
    dates = df["fecha"].astype(str).tolist()
    dts = df["dt"].tolist()
    lags, rec_w, target_streaks, markov, payout = cfg["lags"], cfg["rec_w"], cfg["target_streaks"], cfg["markov"], cfg["payout"]
    
    streak, trigger_miss = 0, 0
    min_idx = max(lags) + rec_w + 2
    for i in range(min_idx, len(nums)):
        actual = nums[i]
        rec_set = set(nums[i-rec_w:i])
        raw_lags = [nums[i-l] for l in lags if i >= l]
        cands_lag = sorted(list(set(raw_lags) - rec_set))
        
        prev_num = nums[i-1]
        if prev_num in markov and markov[prev_num] not in rec_set:
            cands = [markov[prev_num]]
            is_markov = True
        else:
            cands = cands_lag
            is_markov = False
            
        should_bet = (streak in target_streaks and bool(cands)) or is_markov
        peso = calcular_peso_agente(r_name, streak, trigger_miss, payout, cfg)
        
        if should_bet and cands:
            hit = actual in cands
            all_events.append({
                "dt": dts[i],
                "fecha": dates[i],
                "ruleta": r_name,
                "payout": payout,
                "cands_count": len(cands),
                "hit": hit,
                "peso": peso
            })
            
        if cands:
            hit_cond = (actual in cands)
            if streak in target_streaks:
                trigger_miss = 0 if hit_cond else trigger_miss + 1
            streak = 0 if hit_cond else streak + 1

all_events.sort(key=lambda x: x["dt"])

# Agrupar PnL por Día y por Semana (ambos modelos: Plana vs Pesos)
daily_plana = collections.defaultdict(lambda: {"inv": 0.0, "cob": 0.0, "ops": 0, "wins": 0})
daily_pesos = collections.defaultdict(lambda: {"inv": 0.0, "cob": 0.0, "ops": 0, "wins": 0})

for ev in all_events:
    d = ev["fecha"]
    cands_cnt = ev["cands_count"]
    hit = ev["hit"]
    payout = ev["payout"]
    peso = ev["peso"]
    
    # Plana
    cost_p = cands_cnt * 1.00
    cob_p = (1.00 * payout) if hit else 0.0
    daily_plana[d]["inv"] += cost_p
    daily_plana[d]["cob"] += cob_p
    daily_plana[d]["ops"] += 1
    if hit: daily_plana[d]["wins"] += 1
    
    # Pesos
    stk_w = round(max(0.10, min(2.00, 1.00 * (peso / 5.0))), 2)
    cost_w = cands_cnt * stk_w
    cob_w = (stk_w * payout) if hit else 0.0
    daily_pesos[d]["inv"] += cost_w
    daily_pesos[d]["cob"] += cob_w
    daily_pesos[d]["ops"] += 1
    if hit: daily_pesos[d]["wins"] += 1

# Métricas de Días
def analizar_series(d_dict, nombre_modelo):
    sorted_days = sorted(d_dict.keys())
    pnls = [d_dict[d]["cob"] - d_dict[d]["inv"] for d in sorted_days]
    
    dias_ganadores = sum(1 for p in pnls if p > 0)
    dias_perdedores = sum(1 for p in pnls if p < 0)
    dias_neutros = sum(1 for p in pnls if p == 0)
    total_dias = len(pnls)
    
    # Rachas de días perdedores
    rachas_perdida = []
    curr_loss_streak = 0
    for p in pnls:
        if p < 0:
            curr_loss_streak += 1
        else:
            if curr_loss_streak > 0:
                rachas_perdida.append(curr_loss_streak)
            curr_loss_streak = 0
    if curr_loss_streak > 0:
        rachas_perdida.append(curr_loss_streak)
        
    max_dias_loss = max(rachas_perdida) if rachas_perdida else 0
    avg_dias_loss = sum(rachas_perdida) / len(rachas_perdida) if rachas_perdida else 0
    
    # Semanas (agrupar de 7 en 7 días calendario)
    semanas = collections.defaultdict(lambda: {"inv": 0.0, "cob": 0.0, "pnl": 0.0})
    for d in sorted_days:
        dt = datetime.datetime.strptime(d, "%Y-%m-%d").date()
        # Clave año-semana ISO
        iso_year, iso_week, _ = dt.isocalendar()
        sem_key = f"{iso_year}-W{iso_week:02d}"
        p = d_dict[d]["cob"] - d_dict[d]["inv"]
        semanas[sem_key]["inv"] += d_dict[d]["inv"]
        semanas[sem_key]["cob"] += d_dict[d]["cob"]
        semanas[sem_key]["pnl"] += p
        
    sem_pnls = [semanas[k]["pnl"] for k in sorted(semanas.keys())]
    sem_ganadoras = sum(1 for p in sem_pnls if p > 0)
    sem_perdedoras = sum(1 for p in sem_pnls if p < 0)
    sem_neutras = sum(1 for p in sem_pnls if p == 0)
    total_sem = len(sem_pnls)
    
    # Rachas de semanas perdedoras
    rachas_sem_loss = []
    curr_sem_loss = 0
    for p in sem_pnls:
        if p < 0:
            curr_sem_loss += 1
        else:
            if curr_sem_loss > 0:
                rachas_sem_loss.append(curr_sem_loss)
            curr_sem_loss = 0
    if curr_sem_loss > 0:
        rachas_sem_loss.append(curr_sem_loss)
        
    max_sem_loss = max(rachas_sem_loss) if rachas_sem_loss else 0
    avg_sem_loss = sum(rachas_sem_loss) / len(rachas_sem_loss) if rachas_sem_loss else 0
    
    # Peor día y peor semana
    peor_dia_val = min(pnls) if pnls else 0
    peor_dia_idx = sorted_days[pnls.index(peor_dia_val)] if pnls else ""
    peor_sem_val = min(sem_pnls) if sem_pnls else 0
    sorted_sems = sorted(semanas.keys())
    peor_sem_idx = sorted_sems[sem_pnls.index(peor_sem_val)] if sem_pnls else ""
    
    return {
        "modelo": nombre_modelo,
        "total_dias": total_dias,
        "dias_gan": dias_ganadores,
        "dias_perd": dias_perdedores,
        "pct_dias_gan": round(dias_ganadores / total_dias * 100, 1),
        "pct_dias_perd": round(dias_perdedores / total_dias * 100, 1),
        "max_dias_loss": max_dias_loss,
        "avg_dias_loss": round(avg_dias_loss, 2),
        "total_rachas_dias": len(rachas_perdida),
        "peor_dia": peor_dia_val,
        "peor_dia_fecha": peor_dia_idx,
        "total_sem": total_sem,
        "sem_gan": sem_ganadoras,
        "sem_perd": sem_perdedoras,
        "pct_sem_gan": round(sem_ganadoras / total_sem * 100, 1),
        "pct_sem_perd": round(sem_perdedoras / total_sem * 100, 1),
        "max_sem_loss": max_sem_loss,
        "avg_sem_loss": round(avg_sem_loss, 2),
        "total_rachas_sem": len(rachas_sem_loss),
        "peor_sem": peor_sem_val,
        "peor_sem_idx": peor_sem_idx
    }

res_p = analizar_series(daily_plana, "Inversión Plana ($1.00)")
res_w = analizar_series(daily_pesos, "Sistema de Pesos (1 al 10)")

print("=== RESULTADOS FORENSES: DÍAS Y SEMANAS EN PÉRDIDA ===")
for r in [res_p, res_w]:
    print(f"\n--- {r['modelo']} ---")
    print(f"Total Días Operados: {r['total_dias']}")
    print(f"  • Días Ganadores:   {r['dias_gan']} ({r['pct_dias_gan']}%)")
    print(f"  • Días Perdedores:  {r['dias_perd']} ({r['pct_dias_perd']}%)")
    print(f"  • Racha Promedio de Días Perdedores:  {r['avg_dias_loss']} días seguidos")
    print(f"  • Racha Máxima Histórica de Días Pérdida: {r['max_dias_loss']} días seguidos")
    print(f"  • Peor Día Histórico: ${r['peor_dia']:+,.2f} USD ({r['peor_dia_fecha']})")
    print(f"Total Semanas Calendario: {r['total_sem']}")
    print(f"  • Semanas Ganadoras: {r['sem_gan']} ({r['pct_sem_gan']}%)")
    print(f"  • Semanas Perdedoras: {r['sem_perd']} ({r['pct_sem_perd']}%)")
    print(f"  • Racha Promedio Semanas Perdedoras: {r['avg_sem_loss']} semanas seguidas")
    print(f"  • Racha Máxima Semanas Perdedoras:   {r['max_sem_loss']} semanas seguidas")
    print(f"  • Peor Semana Histórica: ${r['peor_sem']:+,.2f} USD ({r['peor_sem_idx']})")

with open(os.path.join(OUTPUT_DIR, "scratch", "resumen_dias_semanas_perdidas.json"), "w") as f:
    json.dump({"plana": res_p, "pesos": res_w}, f, indent=2)
