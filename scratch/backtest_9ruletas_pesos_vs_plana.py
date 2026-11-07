"""
BACKTEST INSTITUCIONAL COMPARATIVO: CARTERA ÉLITE DE 9 RULETAS
Compara sorteo a sorteo durante 2 años:
1. Inversión Plana ($1.00 USD fijo por ficha)
2. Inversión Dinámica por Agente de Ruleta (Ponderada por Peso 1 al 10: $0.20 a $2.00 USD)

Ruletas de la Cartera Élite (9):
1. Lotto Gato (60x)
2. Granja Millonaria Granjazo (60x)
3. Loto Chaima (60x)
4. Guacharo Activo (60x)
5. Mega Animal 40 (30x)
6. Ruleta Royal (30x)
7. Lotto Activo (30x)
8. Gatazo (60x)
9. Monje Millonario (60x)
"""

import os, collections, datetime, json
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
import pandas as pd
import numpy as np

OUTPUT_DIR = r"C:\Users\victo\nuevas_ruletas"

CONFIG_9 = {
    "Lotto Gato": {
        "file": os.path.join(OUTPUT_DIR, "lotto_gato.csv"),
        "payout": 60.0,
        "n_animals": 75,
        "lags": [18, 38, 14],
        "rec_w": 6,
        "target_streaks": [1, 2],
        "wr_optimos": [1, 2],
        "markov": {"14": "0", "27": "15", "3": "7"},
        "emoji": "🐱"
    },
    "Granja Mill. Granjazo": {
        "file": os.path.join(OUTPUT_DIR, "granja_millonaria_granjazo.csv"),
        "payout": 60.0,
        "n_animals": 75,
        "lags": [45, 26, 15],
        "rec_w": 6,
        "target_streaks": [1, 3],
        "wr_optimos": [1, 3],
        "markov": {},
        "emoji": "🚜"
    },
    "Loto Chaima": {
        "file": os.path.join(OUTPUT_DIR, "loto_chaima.csv"),
        "payout": 60.0,
        "n_animals": 75,
        "lags": [49, 41, 35],
        "rec_w": 6,
        "target_streaks": [0, 1],
        "wr_optimos": [0, 1],
        "markov": {"48": "0", "55": "0", "12": "0"},
        "emoji": "🏹"
    },
    "Guacharo Activo": {
        "file": os.path.join(OUTPUT_DIR, "data_vz", "guacharo_activo_2anios.csv"),
        "payout": 60.0,
        "n_animals": 75,
        "lags": [31, 54, 41],
        "rec_w": 8,
        "target_streaks": [1, 3],
        "wr_optimos": [1, 3, 6],
        "markov": {"21": "0", "8": "67", "29": "2"},
        "emoji": "🦇"
    },
    "Mega Animal 40": {
        "file": os.path.join(OUTPUT_DIR, "mega_animal_40.csv"),
        "payout": 30.0,
        "n_animals": 40,
        "lags": [18, 20, 43],
        "rec_w": 8,
        "target_streaks": [1, 2, 3],
        "wr_optimos": [0, 1, 2, 3],
        "markov": {"30": "0", "11": "0", "32": "35"},
        "emoji": "🦏"
    },
    "Ruleta Royal": {
        "file": os.path.join(OUTPUT_DIR, "data_vz", "ruleta_royal_2anios.csv"),
        "payout": 30.0,
        "n_animals": 38,
        "lags": [19, 16, 31],
        "rec_w": 6,
        "target_streaks": [1],
        "wr_optimos": [0, 1, 6],
        "markov": {"25": "22", "8": "27"},
        "emoji": "👑"
    },
    "Lotto Activo": {
        "file": os.path.join(OUTPUT_DIR, "data_vz", "lotto_activo_2anios.csv"),
        "payout": 30.0,
        "n_animals": 38,
        "lags": [20, 18, 15],
        "rec_w": 6,
        "target_streaks": [1, 2],
        "wr_optimos": [0, 1, 2],
        "markov": {"14": "0", "31": "0", "6": "0"},
        "emoji": "🦁"
    },
    "Gatazo": {
        "file": os.path.join(OUTPUT_DIR, "gatazo.csv"),
        "payout": 60.0,
        "n_animals": 75,
        "lags": [35, 9, 20],
        "rec_w": 6,
        "target_streaks": [1],
        "wr_optimos": [1, 11, 12],
        "markov": {"30": "63", "48": "21", "23": "42"},
        "emoji": "🐯"
    },
    "Monje Millonario": {
        "file": os.path.join(OUTPUT_DIR, "monje_millonario.csv"),
        "payout": 60.0,
        "n_animals": 75,
        "lags": [24, 42, 48],
        "rec_w": 6,
        "target_streaks": [0, 1],
        "wr_optimos": [0, 1],
        "markov": {},
        "emoji": "🧘‍♂️"
    }
}

def calcular_peso_agente(r_name, streak, trigger_miss, payout, cfg):
    """
    Agente Cuantitativo de Salud y Ponderación por Ruleta (1 a 10).
    3 dimensiones fundamentales:
    - S_racha: Posición en racha según picos de acierto de esa ruleta (0-4 pts)
    - S_pago: Asimetría del factor de pago (60x vs 30x) (1-3 pts)
    - S_trigger: Dinámica de rebote post-fallo (0-3 pts)
    """
    wr_optimos = cfg["wr_optimos"]
    if streak in wr_optimos:
        s_racha = 4
    elif streak <= 1:
        s_racha = 3
    elif streak <= 5:
        s_racha = 2
    elif streak <= 20:
        s_racha = 1
    else:
        s_racha = 0

    s_pago = 3 if payout >= 60.0 else 2

    if 1 <= trigger_miss <= 3:
        s_trigger = 3
    elif trigger_miss == 0:
        s_trigger = 1
    elif trigger_miss <= 8:
        s_trigger = 2
    else:
        s_trigger = 0

    peso = max(1, min(10, s_racha + s_pago + s_trigger))
    return peso

# 1. Cargar y ordenar cronológicamente todos los sorteos
print("Cargando y unificando sorteos de las 9 ruletas...")
all_events = []

for r_name, cfg in CONFIG_9.items():
    if not os.path.exists(cfg["file"]):
        print(f"[-] No existe {cfg['file']}")
        continue
    df = pd.read_csv(cfg["file"])
    df["dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], errors="coerce")
    df = df.dropna(subset=["dt", "numero"]).sort_values(by="dt").reset_index(drop=True)
    
    nums = [str(x).strip() for x in df["numero"].tolist()]
    dates = df["fecha"].astype(str).tolist()
    horas = df["hora"].astype(str).tolist()
    dts = df["dt"].tolist()
    
    lags = cfg["lags"]
    rec_w = cfg["rec_w"]
    target_streaks = cfg["target_streaks"]
    markov = cfg["markov"]
    payout = cfg["payout"]
    
    streak = 0
    trigger_miss = 0
    
    min_idx = max(lags) + rec_w + 2
    for i in range(min_idx, len(nums)):
        actual = nums[i]
        rec_set = set(nums[i-rec_w:i])
        raw_lags = [nums[i-l] for l in lags if i >= l]
        cands_lag = sorted(list(set(raw_lags) - rec_set))
        
        # Verificar Markov
        prev_num = nums[i-1]
        is_markov = False
        if prev_num in markov and markov[prev_num] not in rec_set:
            cands = [markov[prev_num]]
            is_markov = True
        else:
            cands = cands_lag
            
        should_bet = (streak in target_streaks and bool(cands)) or is_markov
        
        peso = calcular_peso_agente(r_name, streak, trigger_miss, payout, cfg)
        
        if should_bet and cands:
            hit = actual in cands
            all_events.append({
                "dt": dts[i],
                "fecha": dates[i],
                "hora": horas[i],
                "ruleta": r_name,
                "payout": payout,
                "cands_count": len(cands),
                "is_markov": is_markov,
                "hit": hit,
                "streak": streak,
                "trigger_miss": trigger_miss,
                "peso": peso
            })
            
        # Actualizar estados de racha sorteo a sorteo
        if cands:
            hit_cond = (actual in cands)
            if streak in target_streaks:
                if hit_cond:
                    trigger_miss = 0
                else:
                    trigger_miss += 1
            if hit_cond:
                streak = 0
            else:
                streak += 1

# Ordenar toda la línea temporal combinada
all_events.sort(key=lambda x: x["dt"])
print(f"Total oportunidades evaluadas cronológicamente: {len(all_events)}")

# 2. SIMULACIÓN PARALELA: PLANA vs PESOS (1 al 10)
# Modelo Plano: $1.00 USD fijo por ficha
# Modelo Pesos: stake = round(peso / 5.0, 2) ($0.20 a $2.00 USD por ficha)

stats_plana = {
    "inv": 0.0, "cob": 0.0, "pnl": 0.0, "wins": 0, "ops": len(all_events),
    "curve": [], "daily_pnl": collections.defaultdict(float),
    "por_ruleta": collections.defaultdict(lambda: {"inv": 0.0, "cob": 0.0, "wins": 0, "ops": 0})
}

stats_pesos = {
    "inv": 0.0, "cob": 0.0, "pnl": 0.0, "wins": 0, "ops": len(all_events),
    "curve": [], "daily_pnl": collections.defaultdict(float),
    "por_ruleta": collections.defaultdict(lambda: {"inv": 0.0, "cob": 0.0, "wins": 0, "ops": 0, "pesos": []})
}

cum_plana = 0.0
cum_pesos = 0.0

for ev in all_events:
    r_name = ev["ruleta"]
    cands_count = ev["cands_count"]
    payout = ev["payout"]
    hit = ev["hit"]
    d_str = ev["fecha"]
    peso = ev["peso"]
    
    # 1. PLANA
    stake_plana = 1.00
    cost_plana = cands_count * stake_plana
    cob_plana = (stake_plana * payout) if hit else 0.0
    pnl_plana = cob_plana - cost_plana
    
    stats_plana["inv"] += cost_plana
    stats_plana["cob"] += cob_plana
    stats_plana["pnl"] += pnl_plana
    if hit: stats_plana["wins"] += 1
    cum_plana += pnl_plana
    stats_plana["curve"].append(cum_plana)
    stats_plana["daily_pnl"][d_str] += pnl_plana
    stats_plana["por_ruleta"][r_name]["inv"] += cost_plana
    stats_plana["por_ruleta"][r_name]["cob"] += cob_plana
    stats_plana["por_ruleta"][r_name]["ops"] += 1
    if hit: stats_plana["por_ruleta"][r_name]["wins"] += 1
    
    # 2. PESOS (Peso 5 = $1.00 base, Peso 10 = $2.00, Peso 1 = $0.20)
    stake_pesos = round(max(0.10, min(2.00, 1.00 * (peso / 5.0))), 2)
    cost_pesos = cands_count * stake_pesos
    cob_pesos = (stake_pesos * payout) if hit else 0.0
    pnl_pesos = cob_pesos - cost_pesos
    
    stats_pesos["inv"] += cost_pesos
    stats_pesos["cob"] += cob_pesos
    stats_pesos["pnl"] += pnl_pesos
    if hit: stats_pesos["wins"] += 1
    cum_pesos += pnl_pesos
    stats_pesos["curve"].append(cum_pesos)
    stats_pesos["daily_pnl"][d_str] += pnl_pesos
    stats_pesos["por_ruleta"][r_name]["inv"] += cost_pesos
    stats_pesos["por_ruleta"][r_name]["cob"] += cob_pesos
    stats_pesos["por_ruleta"][r_name]["ops"] += 1
    stats_pesos["por_ruleta"][r_name]["pesos"].append(peso)
    if hit: stats_pesos["por_ruleta"][r_name]["wins"] += 1

def compute_drawdown(curve):
    peak = 0.0
    max_dd = 0.0
    for v in curve:
        peak = max(peak, v)
        dd = peak - v
        max_dd = max(max_dd, dd)
    return max_dd

dd_plana = compute_drawdown(stats_plana["curve"])
dd_pesos = compute_drawdown(stats_pesos["curve"])

roi_plana = (stats_plana["pnl"] / stats_plana["inv"] * 100.0) if stats_plana["inv"] > 0 else 0
roi_pesos = (stats_pesos["pnl"] / stats_pesos["inv"] * 100.0) if stats_pesos["inv"] > 0 else 0

pf_plana = stats_plana["cob"] / stats_plana["inv"] if stats_plana["inv"] > 0 else 0
pf_pesos = stats_pesos["cob"] / stats_pesos["inv"] if stats_pesos["inv"] > 0 else 0

wr_global = (stats_plana["wins"] / len(all_events) * 100.0) if all_events else 0

print("\n" + "=" * 90)
print(" 🎯 COMPARATIVA GLOBAL: 9 RULETAS ÉLITE (2 AÑOS HISTÓRICOS)")
print("=" * 90)
print(f"Total Disparos Ejecutados:  {len(all_events):,}")
print(f"Aciertos Totales:           {stats_plana['wins']:,} ({wr_global:.2f}% Win Rate)")
print("-" * 90)
print(f"{'MÉTRICA':<28} | {'MODELO PLANO ($1.00)':<25} | {'SISTEMA DE PESOS (1-10)':<25}")
print("-" * 90)
print(f"{'Inversión Total':<28} | ${stats_plana['inv']:>14,.2f} USD | ${stats_pesos['inv']:>14,.2f} USD")
print(f"{'Cobro Total':<28} | ${stats_plana['cob']:>14,.2f} USD | ${stats_pesos['cob']:>14,.2f} USD")
print(f"{'Beneficio Neto (PnL)':<28} | ${stats_plana['pnl']:>14,.2f} USD | ${stats_pesos['pnl']:>14,.2f} USD")
print(f"{'Retorno de Inversión (ROI)':<28} | {roi_plana:>20.2f}% | {roi_pesos:>20.2f}%")
print(f"{'Profit Factor':<28} | {pf_plana:>21.2f} | {pf_pesos:>21.2f}")
print(f"{'Max Drawdown Histórico':<28} | -${dd_plana:>13,.2f} USD | -${dd_pesos:>13,.2f} USD")
print("=" * 90)

print("\n--- DESGLOSE POR RULETA ---")
print(f"{'RULETA':<24} | {'DISPAROS':<8} | {'WR %':<6} | {'PNL PLANO':<12} | {'PNL PESOS':<12} | {'ROI PESOS':<10} | {'PESO MED'}")
print("-" * 90)

for r_name in CONFIG_9.keys():
    dp = stats_plana["por_ruleta"][r_name]
    dw = stats_pesos["por_ruleta"][r_name]
    ops_r = dp["ops"]
    if ops_r == 0: continue
    wr_r = dp["wins"] / ops_r * 100
    pnl_p = dp["cob"] - dp["inv"]
    pnl_w = dw["cob"] - dw["inv"]
    roi_w = pnl_w / dw["inv"] * 100 if dw["inv"] > 0 else 0
    avg_peso = sum(dw["pesos"]) / len(dw["pesos"]) if dw["pesos"] else 0
    emoji = CONFIG_9[r_name]["emoji"]
    print(f"{emoji} {r_name:<21} | {ops_r:>8} | {wr_r:>5.1f}% | ${pnl_p:>+10,.2f} | ${pnl_w:>+10,.2f} | {roi_w:>+8.1f}% | {avg_peso:>5.1f}/10")

# Guardar resultados para artefacto
res_dict = {
    "total_ops": len(all_events),
    "total_wins": stats_plana["wins"],
    "win_rate": wr_global,
    "plana": {
        "inv": stats_plana["inv"],
        "cob": stats_plana["cob"],
        "pnl": stats_plana["pnl"],
        "roi": roi_plana,
        "profit_factor": pf_plana,
        "max_dd": dd_plana
    },
    "pesos": {
        "inv": stats_pesos["inv"],
        "cob": stats_pesos["cob"],
        "pnl": stats_pesos["pnl"],
        "roi": roi_pesos,
        "profit_factor": pf_pesos,
        "max_dd": dd_pesos
    }
}

with open(os.path.join(OUTPUT_DIR, "scratch", "resumen_backtest_9ruletas.json"), "w") as f:
    json.dump(res_dict, f, indent=2)
