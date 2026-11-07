"""
========================================================================================
 MOTOR DE PRUEBAS DE INVERSIÓN INTELIGENTE (2 AÑOS DE DATA)
========================================================================================
Evalúa 6 modelos de inversión inteligente sobre las 7 ruletas oficiales:
 1. Baseline Actual ($200 USD inicial, Full Kelly + Grossman-Zhou).
 2. Modelo 1: Priorización Estática por Calidad Intrínseca (Gatazo/Monje/Guacharo/Royal boost 1.25x, resto 0.85x).
 3. Modelo 2: Full Kelly Teórico Exacto (calibrado al edge exacto de cada ruleta a 2 años).
 4. Modelo 3: Impulso por Rebound Momentum (aumenta stake en disparos de racha 1 a 3 post-fallo donde el ROI sube a +80%).
 5. Modelo 4: Priorización Dinámica en Co-Ocurrencia (cuando 2+ ruletas disparan a la misma hora, asigna más capital a la ruleta con mayor ROI).
 6. Modelo 5: Inversión Inteligente Integral (Combina Kelly Calibrado + Priorización en Co-Ocurrencia).
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

# F_units calibradas al Kelly teórico exacto:
KELLY_OPT_F = {
    "Gatazo": 0.01350,       # Kelly óptimo 0.01658 (ajuste conservador al 80%)
    "Monje Millonario": 0.01100, # Kelly óptimo 0.01329 (ajuste conservador)
    "Guacharo Activo": 0.00706,
    "Mega Animal 40": 0.00950,
    "Ruleta Royal": 0.00900,
    "Lotto Activo": 0.00820,
    "La Granjita": 0.00484
}

def load_data():
    signals = []
    
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
        min_idx = max(lags) + 6
        
        streak = 0
        trigger_consec_misses = 0
        
        for i in range(min_idx, len(nums)):
            actual = nums[i]
            rec6 = set(nums[i-6:i])
            cands = sorted(list({nums[i-l] for l in lags} - rec6))
            cost = len(cands)
            hit = (actual in cands)
            
            if streak in target_streaks and cost > 0:
                signals.append({
                    "dt": df.iloc[i]["dt"],
                    "fecha": df.iloc[i]["fecha"],
                    "hora": df.iloc[i]["hora"],
                    "ruleta": r_name,
                    "emoji": cfg["emoji"],
                    "payout": payout,
                    "f_unit": f_unit,
                    "f_unit_opt": KELLY_OPT_F.get(r_name, f_unit),
                    "cost": cost,
                    "hit": hit,
                    "trigger_consec_misses": trigger_consec_misses
                })
                if hit:
                    trigger_consec_misses = 0
                else:
                    trigger_consec_misses += 1
                    
            if hit:
                streak = 0
            else:
                streak += 1
                
    signals.sort(key=lambda x: x["dt"])
    return signals

def simulate(signals, model_id, init_bankroll=200.0, mdd_floor=0.40, min_bet=0.10):
    bankroll = init_bankroll
    peak = init_bankroll
    max_dd = 0.0
    total_inv = 0.0
    total_cob = 0.0
    wins = 0
    losses = 0
    
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
        
        # Rankings de prioridad para co-ocurrencia
        roi_rank = {
            "Gatazo": 1.95, "Monje Millonario": 1.76, "Guacharo Activo": 1.39,
            "Mega Animal 40": 1.31, "Ruleta Royal": 1.26, "Lotto Activo": 1.23, "La Granjita": 1.14
        }
        
        for ev in active:
            r_name = ev["ruleta"]
            base_f = ev["f_unit"]
            misses = ev["trigger_consec_misses"]
            
            if model_id == "baseline":
                weight = 1.0
                f_to_use = base_f
                
            elif model_id == "priorizacion_estatica":
                # Boost a ruletas de alto ROI (>50% ROI histórico)
                weight = 1.25 if r_name in ["Gatazo", "Monje Millonario", "Guacharo Activo"] else 0.85
                f_to_use = base_f
                
            elif model_id == "kelly_teorico_exacto":
                # Usar la fracción óptima matemáticamente calibrada
                weight = 1.0
                f_to_use = ev["f_unit_opt"]
                
            elif model_id == "rebound_momentum":
                # Aumentar peso cuando el disparador lleva entre 1 y 3 fallos (zona de máximo rebote: WR 13-14%, ROI +89%)
                if 1 <= misses <= 3:
                    weight = 1.25
                elif misses == 0:
                    weight = 0.85  # Post-acierto inmediato (ROI solo +2.6%)
                else:
                    weight = 1.00
                f_to_use = base_f
                
            elif model_id == "coocurrencia_inteligente":
                # Si hay más de 1 ruleta al mismo tiempo, asignar más a la de mayor rentabilidad
                if len(active) > 1:
                    my_score = roi_rank.get(r_name, 1.2)
                    avg_score = np.mean([roi_rank.get(x["ruleta"], 1.2) for x in active])
                    weight = min(1.35, max(0.70, my_score / avg_score))
                else:
                    weight = 1.0
                f_to_use = base_f
                
            elif model_id == "inversion_integral":
                # Combina: Kelly Calibrado + Rebound Momentum + Priorización en Coocurrencia
                f_to_use = ev["f_unit_opt"]
                w_rebound = 1.20 if (1 <= misses <= 3) else (0.85 if misses == 0 else 1.0)
                if len(active) > 1:
                    my_score = roi_rank.get(r_name, 1.2)
                    avg_score = np.mean([roi_rank.get(x["ruleta"], 1.2) for x in active])
                    w_cooc = min(1.30, max(0.75, my_score / avg_score))
                else:
                    w_cooc = 1.0
                weight = w_rebound * w_cooc
            else:
                weight = 1.0
                f_to_use = base_f
                
            base_stake = bankroll * f_to_use
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
    mult = round(bankroll / init_bankroll, 2)
    
    return {
        "model_id": model_id,
        "final_bankroll": bankroll,
        "pnl_neto": pnl_neto,
        "roi_neto": roi_neto,
        "multiplicador": mult,
        "max_dd": round(max_dd, 2),
        "total_inv": round(total_inv, 2),
        "total_cob": round(total_cob, 2),
        "peak": round(peak, 2)
    }

def main():
    signals = load_data()
    print("=" * 115)
    print(" 🧪 PRUEBA EXHAUSTIVA DE INVERSIÓN INTELIGENTE (2 AÑOS DE HISTORIA - 7 RULETAS)")
    print("    Capital Inicial: $200.00 USD | MDD Floor: 40% | Min Bet: $0.10 USD | Total Sorteos Sniper: 2,881")
    print("=" * 115)
    
    models = [
        ("baseline", "1. BASELINE ACTUAL (Full Kelly + Grossman-Zhou Estándar)"),
        ("priorizacion_estatica", "2. PRIORIZACIÓN ALTO ROI (Gatazo, Monje, Guácharo 1.25x | Resto 0.85x)"),
        ("kelly_teorico_exacto", "3. KELLY TEÓRICO EXACTO (Calibración pura del f* por ruleta)"),
        ("rebound_momentum", "4. REBOUND MOMENTUM (Boost 1.25x en Fallos 1 a 3 donde ROI = +89%)"),
        ("coocurrencia_inteligente", "5. PRIORIZACIÓN EN CO-OCURRENCIA (Favorece mayor Sharpe en sorteos simultáneos)"),
        ("inversion_integral", "6. INVERSIÓN INTELIGENTE INTEGRAL (Kelly Calibrado + Rebound + Co-Ocurrencia)")
    ]
    
    results = []
    for m_id, m_name in models:
        r = simulate(signals, m_id, init_bankroll=200.0, mdd_floor=0.40, min_bet=0.10)
        r["name"] = m_name
        results.append(r)
        
    for r in results:
        diff_cash = r['final_bankroll'] - results[0]['final_bankroll']
        diff_str = f"(+{diff_cash:+,.2f} USD vs Baseline)" if diff_cash != 0 else "(Referencia)"
        print(f"\n{r['name']}:")
        print(f"  • Capital Final:      ${r['final_bankroll']:>12,.2f} USD  {diff_str}")
        print(f"  • Ganancia Neta:      +${r['pnl_neto']:>11,.2f} USD (Multiplicador: {r['multiplicador']:>6.2f}x)")
        print(f"  • Retorno (ROI):      +{r['roi_neto']:>11.2f}%")
        print(f"  • Pico Máximo (ATH):  ${r['peak']:>12,.2f} USD")
        print(f"  • Máximo Drawdown:     {r['max_dd']:>11.2f}% (Piso límite: 40.0%)")
        print(f"  • Total Invertido:    ${r['total_inv']:>12,.2f} USD")
        
    print("\n" + "=" * 115)

if __name__ == "__main__":
    main()
