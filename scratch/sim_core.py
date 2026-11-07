import os
import sys
import pandas as pd
import numpy as np

VZ_DIR = r"C:\Users\victo\nuevas_ruletas\data_vz"
ROOT_DIR = r"C:\Users\victo\nuevas_ruletas"

RULETAS = {
    "Lotto Activo": {"file": os.path.join(VZ_DIR, "lotto_activo_2anios.csv"), "payout": 30.0, "current_lags": [20, 18, 14], "rec_w": 6, "target_streaks": [1]},
    "La Granjita": {"file": os.path.join(VZ_DIR, "la_granjita_2anios.csv"), "payout": 30.0, "current_lags": [15, 17], "rec_w": 8, "target_streaks": [1]},
    "Ruleta Royal": {"file": os.path.join(VZ_DIR, "ruleta_royal_2anios.csv"), "payout": 30.0, "current_lags": [16, 19, 31], "rec_w": 6, "target_streaks": [1]},
    "Guacharo Activo": {"file": os.path.join(VZ_DIR, "guacharo_activo_2anios.csv"), "payout": 60.0, "current_lags": [31, 41, 25, 42, 35], "rec_w": 8, "target_streaks": [1]},
    "Gatazo": {"file": os.path.join(ROOT_DIR, "gatazo.csv"), "payout": 60.0, "current_lags": [35, 22, 20], "rec_w": 6, "target_streaks": [1, 2]},
    "Mega Animal 40": {"file": os.path.join(ROOT_DIR, "mega_animal_40.csv"), "payout": 30.0, "current_lags": [18, 21, 37], "rec_w": 8, "target_streaks": [1]},
    "Monje Millonario": {"file": os.path.join(ROOT_DIR, "monje_millonario.csv"), "payout": 60.0, "current_lags": [24, 35, 37], "rec_w": 6, "target_streaks": [1]},
    "Lotto Activo RD": {"file": os.path.join(ROOT_DIR, "lotto_activo_rd_lotoven_completo.csv"), "payout": 30.0, "current_lags": [21, 39, 50], "rec_w": 6, "target_streaks": [1]},
    "Lotto Gato": {"file": os.path.join(ROOT_DIR, "lotto_gato.csv"), "payout": 30.0, "current_lags": [19, 38, 16], "rec_w": 6, "target_streaks": [1]},
    "Loto Chaima": {"file": os.path.join(ROOT_DIR, "loto_chaima.csv"), "payout": 40.0, "current_lags": [35, 29, 38], "rec_w": 6, "target_streaks": [1]},
    "Selva Plus": {"file": os.path.join(VZ_DIR, "selva_plus_2anios.csv"), "payout": 80.0, "current_lags": [20, 24, 36], "rec_w": 6, "target_streaks": [1]}
}

def simulate_sniper_strategy(df, lags, rec_w, target_streaks, use_anti_cluster, payout,
                             adaptive_rec_mode="none"):
    """
    Simula la estrategia exacta sorteo a sorteo.
    adaptive_rec_mode:
      - 'none': rec_w fijo
      - 'intraday_freq': si el animal ya salió hoy, ventana de purga extendida
      - 'dynamic_k': rec_w escala con la dispersión
    """
    nums = df['numero'].tolist()
    fechas = df['fecha'].tolist() if 'fecha' in df.columns else [''] * len(nums)
    
    total = len(nums)
    min_idx = max(max(lags), 20)
    
    streak = 0
    trade_opportunities = 0
    trades_executed = 0
    trades_won = 0
    total_cost_fichas = 0
    total_payout_collected = 0
    
    seen_today = set()
    last_fecha = None
    prev_was_repeat = False
    
    cands_counts = []
    
    for i in range(min_idx, total):
        fecha = fechas[i]
        actual = nums[i]
        
        if fecha != last_fecha:
            seen_today = set()
            last_fecha = fecha
            prev_was_repeat = False
            
        # Determinar conjunto de purga
        if adaptive_rec_mode == "none":
            rec_set = set(nums[i - rec_w:i])
        elif adaptive_rec_mode == "intraday_freq":
            # purga base rec_w + purga de cualquier animal que ya haya salido 2 o más veces hoy
            rec_set = set(nums[i - rec_w:i])
            # contar frecuencias intradía
            # cualquier animal que ya salió hoy se purga si rec_w_extended
            rec_set = rec_set.union({n for n in seen_today if nums[i - max(rec_w, 10):i].count(n) >= 1})
        elif adaptive_rec_mode == "rec_w_plus_today_repeats":
            # Si un animal ya repitió hoy (ha salido >= 2 veces hoy), queda vetado
            intraday_repeats = set()
            day_history = nums[max(0, i - 15):i] # aproximado intradía si fecha cambia
            rec_set = set(nums[i - rec_w:i])
        else:
            rec_set = set(nums[i - rec_w:i])
            
        # Candidatos de los lags
        raw_cands = [nums[i - l] for l in lags if i >= l]
        cands = sorted(list(set(raw_cands) - rec_set))
        cost = len(cands)
        
        is_repeat_now = (actual in seen_today)
        skip_shot = bool(use_anti_cluster and prev_was_repeat)
        
        hit = (actual in cands) if cost > 0 else False
        
        # Evaluar racha y disparo
        if cost > 0 and not skip_shot:
            if streak in target_streaks:
                trades_executed += 1
                total_cost_fichas += cost
                cands_counts.append(cost)
                if hit:
                    trades_won += 1
                    total_payout_collected += payout
                    
            if hit:
                streak = 0
            else:
                streak += 1
        elif cost > 0 and skip_shot:
            # Inhibido por AntiClustering
            if hit:
                streak = 0
            else:
                streak += 1
        else:
            # cost == 0 (todos purgados)
            # Racha no se rompe
            pass
            
        seen_today.add(actual)
        prev_was_repeat = is_repeat_now

    wr = (trades_won / trades_executed * 100.0) if trades_executed > 0 else 0.0
    avg_cands = (total_cost_fichas / trades_executed) if trades_executed > 0 else 0.0
    pnl = total_payout_collected - total_cost_fichas
    roi = (pnl / total_cost_fichas * 100.0) if total_cost_fichas > 0 else 0.0
    fpr_r1 = (100.0 - wr)
    be_rate = (avg_cands / payout * 100.0) if payout > 0 else 0.0
    
    return {
        "trades": trades_executed,
        "wins": trades_won,
        "wr": wr,
        "avg_cands": avg_cands,
        "cost": total_cost_fichas,
        "payout": total_payout_collected,
        "pnl": pnl,
        "roi": roi,
        "fpr_r1": fpr_r1,
        "be_rate": be_rate
    }

print("Simulador cargado correctamente.")
