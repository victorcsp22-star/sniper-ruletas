"""
========================================================================================
 INVESTIGACIÓN PROFUNDA: CONDICIÓN ÓPTIMA DEL PATRÓN Y PRIORIZACIÓN INTELIGENTE
========================================================================================
Analiza en detalle:
 1. ¿Cómo se comporta el patrón según la calidad intrínseca de cada ruleta (Ranking Sharpe / ROI)?
 2. ¿Existe un ciclo de rebote dentro del propio disparador (trigger misses)?
 3. ¿Qué pasa si aplicamos una asignación de capital proporcional a la ventaja histórica (Sharpe / Kelly ponderado por ruleta)?
 4. ¿Qué pasa si combinamos la priorización de ruletas de Grado A (Royal, Guácharo, Gatazo, Monje) sobre las de menor rendimiento?
========================================================================================
"""

import os
import sys
import numpy as np
import pandas as pd

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

VZ_DIR = r"C:\Users\victo\.gemini\antigravity\scratch\lotto_activo_bot"
NEW_DIR = r"C:\Users\victo\nuevas_ruletas"

RULETAS = {
    "Lotto Activo": {"file": os.path.join(VZ_DIR, "lotto_activo_2anios.csv"), "lags": [20, 18, 14], "payout": 30.0, "target_streaks": [1], "f_unit": 0.00900, "emoji": "🦁"},
    "La Granjita": {"file": os.path.join(VZ_DIR, "la_granjita_2anios.csv"), "lags": [15, 17], "payout": 30.0, "target_streaks": [1], "f_unit": 0.00484, "emoji": "🐸"},
    "Ruleta Royal": {"file": os.path.join(VZ_DIR, "ruleta_royal_2anios.csv"), "lags": [16, 19, 31], "payout": 30.0, "target_streaks": [1], "f_unit": 0.00826, "emoji": "👑"},
    "Guacharo Activo": {"file": os.path.join(VZ_DIR, "guacharo_activo_2anios.csv"), "lags": [31, 41, 25, 42, 35], "payout": 60.0, "target_streaks": [1], "f_unit": 0.00680, "emoji": "🦇"},
    "Gatazo": {"file": os.path.join(NEW_DIR, "gatazo.csv"), "lags": [35, 22, 20], "payout": 60.0, "target_streaks": [1, 2], "f_unit": 0.00900, "emoji": "🐯"},
    "Mega Animal 40": {"file": os.path.join(NEW_DIR, "mega_animal_40.csv"), "lags": [18, 21, 37], "payout": 30.0, "target_streaks": [1], "f_unit": 0.00800, "emoji": "🦏"},
    "Monje Millonario": {"file": os.path.join(NEW_DIR, "monje_millonario.csv"), "lags": [24, 35, 37], "payout": 60.0, "target_streaks": [1], "f_unit": 0.00700, "emoji": "🧘‍♂️"}
}

def load_data():
    signals = []
    r_stats = {}
    
    for r_name, cfg in RULETAS.items():
        if not os.path.exists(cfg["file"]):
            continue
        df = pd.read_csv(cfg["file"], dtype={"numero": str})
        df["numero"] = df["numero"].astype(str).str.strip()
        df["dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        df = df.dropna(subset=["dt"]).sort_values("dt").reset_index(drop=True)
        
        nums = df["numero"].tolist()
        lags = cfg["lags"]
        payout = cfg["payout"]
        target_streaks = cfg["target_streaks"]
        f_unit = cfg["f_unit"]
        be_rate = (1.0 / payout) * 100.0
        min_idx = max(lags) + 6
        
        streak = 0
        r_sigs = []
        for i in range(min_idx, len(nums)):
            actual = nums[i]
            rec6 = set(nums[i-6:i])
            cands = sorted(list({nums[i-l] for l in lags} - rec6))
            cost = len(cands)
            hit = (actual in cands)
            
            if streak in target_streaks and cost > 0:
                sig_item = {
                    "dt": df.iloc[i]["dt"],
                    "fecha": df.iloc[i]["fecha"],
                    "hora": df.iloc[i]["hora"],
                    "ruleta": r_name,
                    "emoji": cfg["emoji"],
                    "payout": payout,
                    "f_unit": f_unit,
                    "be_rate": be_rate,
                    "cost": cost,
                    "hit": hit
                }
                signals.append(sig_item)
                r_sigs.append(sig_item)
                
            streak = 0 if hit else (streak + 1)
            
        # Calcular estadísticas globales de la ruleta
        if r_sigs:
            tot = len(r_sigs)
            hits = sum(1 for s in r_sigs if s["hit"])
            tot_cost = sum(s["cost"] for s in r_sigs)
            tot_cob = sum(s["payout"] for s in r_sigs if s["hit"])
            roi = (tot_cob - tot_cost) / tot_cost * 100.0
            wr = hits / tot * 100.0
            r_stats[r_name] = {
                "tot": tot, "hits": hits, "wr": wr, "roi": roi, "be_rate": be_rate,
                "profit_factor": (tot_cob / tot_cost) if tot_cost > 0 else 1.0
            }
            
    signals.sort(key=lambda x: x["dt"])
    return signals, r_stats

def run_simulation(signals, r_stats, strategy_name, init_bankroll=200.0, mdd_floor=0.40, min_bet=0.10):
    bankroll = init_bankroll
    peak = init_bankroll
    max_dd = 0.0
    total_inv = 0.0
    total_cob = 0.0
    wins = 0
    losses = 0
    
    # Agrupar por timestamp
    from collections import defaultdict
    time_groups = defaultdict(list)
    for s in signals:
        time_groups[s["dt"]].append(s)
        
    for dt in sorted(time_groups.keys()):
        active = time_groups[dt]
        
        peak = max(peak, bankroll)
        floor = (1.0 - mdd_floor) * peak
        cushion = max(0.0, bankroll - floor)
        gz_mult = min(1.0, max(0.0, cushion / (mdd_floor * peak))) if (mdd_floor * peak) > 0 else 1.0
        
        cur_dd = (peak - bankroll) / peak * 100.0 if peak > 0 else 0.0
        max_dd = max(max_dd, cur_dd)
        
        # Calcular ponderación inteligente para cada ruleta
        for ev in active:
            r_name = ev["ruleta"]
            base_f = ev["f_unit"]
            p_factor = r_stats[r_name]["profit_factor"]
            roi = r_stats[r_name]["roi"]
            
            if strategy_name == "baseline":
                weight = 1.0
                
            elif strategy_name == "priorizacion_roi":
                # Ponderación según la rentabilidad intrínseca del patrón en esa ruleta:
                # Ruletas con ROI > 50% (Royal, Guácharo, Gatazo, Monje): 1.25x
                # Ruletas con ROI 15% a 50% (Lotto Activo, Mega Animal, La Granjita): 0.85x
                if roi >= 50.0:
                    weight = 1.25
                else:
                    weight = 0.85
                    
            elif strategy_name == "priorizacion_sharpe":
                # Ponderación proporcional al Profit Factor normalizado
                # Promedio del Profit Factor es ~1.40
                weight = min(1.40, max(0.60, p_factor / 1.35))
                
            elif strategy_name == "elite_overweight":
                # Sobreponderar el cuarteto élite (Royal, Guácharo, Gatazo, Monje) con 1.30x
                # Mantener las demás en 0.75x
                if r_name in ["Ruleta Royal", "Guacharo Activo", "Gatazo", "Monje Millonario"]:
                    weight = 1.30
                else:
                    weight = 0.75
                    
            elif strategy_name == "canasta_optima_boost":
                # Boost cuando la canasta de candidatos tiene entre 2 y 4 animales (zona de máximo edge)
                # Si cost in [2, 3, 4] -> 1.15x; si 1 o 5+ -> 0.80x
                if ev["cost"] in [2, 3, 4]:
                    weight = 1.15
                else:
                    weight = 0.80
                    
            elif strategy_name == "combo_inteligente":
                # Combina Priorización Élite + Canasta Óptima
                w_elite = 1.25 if r_name in ["Ruleta Royal", "Guacharo Activo", "Gatazo", "Monje Millonario"] else 0.80
                w_canasta = 1.10 if ev["cost"] in [2, 3, 4] else 0.85
                weight = w_elite * w_canasta
            else:
                weight = 1.0
                
            base_stake = bankroll * base_f
            stake_unit = round(max(min_bet, base_stake * gz_mult * weight), 2)
            total_bet = round(stake_unit * ev["cost"], 2)
            
            if total_bet > bankroll:
                stake_unit = round(max(min_bet, bankroll / ev["cost"]), 2)
                total_bet = round(stake_unit * ev["cost"], 2)
                if total_bet > bankroll:
                    total_bet = bankroll
                    
            if ev["hit"]:
                cobrado = round(stake_unit * ev["payout"], 2)
                pnl = round(cobrado - total_bet, 2)
                wins += 1
            else:
                cobrado = 0.0
                pnl = -total_bet
                losses += 1
                
            bankroll = round(bankroll + pnl, 2)
            total_inv = round(total_inv + total_bet, 2)
            total_cob = round(total_cob + cobrado, 2)
            peak = max(peak, bankroll)
            
            cur_dd = (peak - bankroll) / peak * 100.0 if peak > 0 else 0.0
            max_dd = max(max_dd, cur_dd)
            
    pnl_neto = round(bankroll - init_bankroll, 2)
    roi_neto = round((total_cob - total_inv) / total_inv * 100.0, 2) if total_inv > 0 else 0.0
    
    return {
        "strategy": strategy_name,
        "final_bankroll": bankroll,
        "pnl_neto": pnl_neto,
        "roi_neto": roi_neto,
        "multiplicador": round(bankroll / init_bankroll, 2),
        "max_dd": round(max_dd, 2),
        "total_inv": round(total_inv, 2),
        "total_cob": round(total_cob, 2),
        "peak": round(peak, 2)
    }

def main():
    signals, r_stats = load_data()
    print("=" * 110)
    print(" 🏆 PERFIL HISTÓRICO DE CALIDAD DE CADA RULETA (2 AÑOS):")
    print("=" * 110)
    for r_name, st in sorted(r_stats.items(), key=lambda x: x[1]["roi"], reverse=True):
        print(f"  {r_name:<20}: Disparos: {st['tot']:>4} | WR: {st['wr']:>5.2f}% (BE: {st['be_rate']:>4.2f}%) | ROI: {st['roi']:>+6.2f}% | Profit Factor: {st['profit_factor']:.2f}x")
    print("=" * 110)
    
    strats = [
        ("baseline", "1. BASELINE ACTUAL (Full Kelly + Grossman-Zhou sin ponderación)"),
        ("priorizacion_roi", "2. PRIORIZACIÓN POR ROI HISTÓRICO (>50% -> 1.25x, <50% -> 0.85x)"),
        ("priorizacion_sharpe", "3. PRIORIZACIÓN POR PROFIT FACTOR DINÁMICO"),
        ("elite_overweight", "4. PRIORIZACIÓN ÉLITE (Royal, Guácharo, Gatazo, Monje: 1.30x | Resto: 0.75x)"),
        ("canasta_optima_boost", "5. CONDICIÓN ÓPTIMA DE CANASTA (2-4 fichas -> 1.15x | 1 ó 5+ -> 0.80x)"),
        ("combo_inteligente", "6. COMBO INTELIGENTE (Priorización Élite + Canasta Óptima)")
    ]
    
    print("\n" + "=" * 110)
    print(" 🚀 RESULTADOS DE LA PRUEBA A 2 AÑOS ($200 USD INICIAL):")
    print("=" * 110)
    
    for s_id, s_title in strats:
        res = run_simulation(signals, r_stats, s_id, init_bankroll=200.0, mdd_floor=0.40, min_bet=0.10)
        print(f"\n{s_title}:")
        print(f"  • Capital Final:      ${res['final_bankroll']:>12,.2f} USD (Pico ATH: ${res['peak']:>12,.2f})")
        print(f"  • Ganancia Neta (PnL):+${res['pnl_neto']:>11,.2f} USD (Multiplicador: {res['multiplicador']:>6.2f}x)")
        print(f"  • Rentabilidad (ROI): +{res['roi_neto']:>11.2f}%")
        print(f"  • Drawdown Máximo:     {res['max_dd']:>11.2f}%")
        print(f"  • Total Invertido:    ${res['total_inv']:>12,.2f} USD")
    print("=" * 110)

if __name__ == "__main__":
    main()
