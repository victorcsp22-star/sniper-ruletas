"""
========================================================================================
 MOTOR DE BACKTEST COMPARATIVO: INVERSIÓN INTELIGENTE POR ESTADO DEL PATRÓN (2 AÑOS)
========================================================================================
Compara rigurosamente 4 variantes de gestión de capital partiendo de $200.00 USD:
  1. BASELINE: Full Kelly + Colchón Grossman-Zhou actual (sin modulación).
  2. MODELO A (Modulación Proporcional de Salud):
     Multiplica la apuesta por el ratio de salud dinámico:
     - Salud >= 1.5x BE -> 1.25x Kelly
     - Salud 1.0x a 1.5x BE -> 1.00x Kelly
     - Salud < 1.0x BE -> 0.40x Kelly (defensivo)
  3. MODELO B (Priorización Dinámica de Ruletas en Co-Ocurrencia):
     Prioriza el capital disponible en la ruleta con mayor índice de salud.
  4. MODELO C (Filtro Sniper Óptimo + Modulación):
     Excluye o reduce a mínimo ($0.10) cuando la salud está por debajo del break-even.
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

def load_all_events(window_size=20):
    all_events = []
    
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
        r_history_hits = []
        
        for i in range(min_idx, len(nums)):
            actual = nums[i]
            rec6 = set(nums[i-6:i])
            cands = sorted(list({nums[i-l] for l in lags} - rec6))
            cost = len(cands)
            hit = (actual in cands)
            
            if streak in target_streaks and cost > 0:
                # Calcular salud reciente
                w = r_history_hits[-window_size:] if len(r_history_hits) >= window_size else r_history_hits
                w_hits = sum(w)
                w_trials = len(w)
                recent_wr = (w_hits / w_trials * 100.0) if w_trials > 0 else (be_rate * 1.5)
                health_ratio = recent_wr / be_rate
                
                all_events.append({
                    "dt": df.iloc[i]["dt"],
                    "fecha": df.iloc[i]["fecha"],
                    "hora": df.iloc[i]["hora"],
                    "ruleta": r_name,
                    "payout": payout,
                    "f_unit": f_unit,
                    "be_rate": be_rate,
                    "cands_count": cost,
                    "hit": hit,
                    "recent_wr": recent_wr,
                    "health_ratio": health_ratio,
                    "hist_len": len(r_history_hits)
                })
                r_history_hits.append(hit)
                
            streak = 0 if hit else (streak + 1)
            
    all_events.sort(key=lambda x: x["dt"])
    return all_events

def run_simulation(events, mode="baseline", init_bankroll=200.0, mdd_floor=0.40, min_bet=0.10):
    bankroll = init_bankroll
    peak = init_bankroll
    max_dd = 0.0
    total_inv = 0.0
    total_cob = 0.0
    wins = 0
    losses = 0
    curve = []
    
    # Agrupar eventos por timestamp para manejar co-ocurrencia simultánea
    from collections import defaultdict
    time_groups = defaultdict(list)
    for ev in events:
        time_groups[ev["dt"]].append(ev)
        
    for dt in sorted(time_groups.keys()):
        active_draws = time_groups[dt]
        
        # Actualizar pico y colchón Grossman-Zhou
        peak = max(peak, bankroll)
        floor = (1.0 - mdd_floor) * peak
        cushion = max(0.0, bankroll - floor)
        gz_mult = min(1.0, max(0.0, cushion / (mdd_floor * peak))) if (mdd_floor * peak) > 0 else 1.0
        
        if gz_mult <= 0.001 and bankroll <= min_bet:
            break
            
        cur_dd = (peak - bankroll) / peak * 100.0 if peak > 0 else 0.0
        max_dd = max(max_dd, cur_dd)
        
        # Calcular multiplicadores según la variante
        draw_orders = []
        for ev in active_draws:
            hr = ev["health_ratio"]
            base_f = ev["f_unit"]
            
            if mode == "baseline":
                health_mult = 1.0
            elif mode == "modulacion_suave":
                # Si health >= 1.5 -> 1.20x; si 1.0 a 1.5 -> 1.0x; si < 1.0 -> 0.50x
                if hr >= 1.5:
                    health_mult = 1.20
                elif hr >= 1.0:
                    health_mult = 1.00
                else:
                    health_mult = 0.50
            elif mode == "modulacion_fuerte":
                # Más agresivo en estado óptimo y más defensivo en degradación
                if hr >= 1.5:
                    health_mult = 1.35
                elif hr >= 1.0:
                    health_mult = 0.90
                else:
                    health_mult = 0.30
            elif mode == "filtro_exclusivo_optimo":
                # Si el patrón está degradado (< 1.0x BE), solo apuesta el mínimo $0.10 (modo centinela)
                if hr >= 1.5:
                    health_mult = 1.25
                elif hr >= 1.0:
                    health_mult = 1.00
                else:
                    health_mult = 0.05  # Casi cero (irá a min_bet $0.10)
            else:
                health_mult = 1.0
                
            draw_orders.append((ev, base_f, health_mult, hr))
            
        # Si hay co-ocurrencia y modo priorización, ordenar por salud descendente
        if mode in ["modulacion_suave", "modulacion_fuerte", "filtro_exclusivo_optimo"]:
            draw_orders.sort(key=lambda x: x[3], reverse=True)
            
        # Ejecutar apuestas del sorteo
        for ev, base_f, h_mult, hr in draw_orders:
            base_stake = bankroll * base_f
            stake_unit = round(max(min_bet, base_stake * gz_mult * h_mult), 2)
            total_bet = round(stake_unit * ev["cands_count"], 2)
            
            # Limitar a que no exceda el bankroll disponible
            if total_bet > bankroll:
                stake_unit = round(max(min_bet, bankroll / ev["cands_count"]), 2)
                total_bet = round(stake_unit * ev["cands_count"], 2)
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
            
            curve.append({"dt": ev["dt"], "saldo": bankroll, "peak": peak, "dd": cur_dd})
            
    pnl_neto = round(bankroll - init_bankroll, 2)
    roi_neto = round((total_cob - total_inv) / total_inv * 100.0, 2) if total_inv > 0 else 0.0
    mult = round(bankroll / init_bankroll, 2)
    
    return {
        "mode": mode,
        "init_bankroll": init_bankroll,
        "final_bankroll": bankroll,
        "pnl_neto": pnl_neto,
        "roi_neto": roi_neto,
        "multiplicador": mult,
        "max_dd": round(max_dd, 2),
        "total_jugadas": len(curve),
        "aciertos": wins,
        "fallos": losses,
        "win_rate": round(wins / len(curve) * 100.0, 2) if curve else 0.0,
        "total_inv": round(total_inv, 2),
        "total_cob": round(total_cob, 2),
        "peak": round(peak, 2)
    }

def main():
    print("=" * 110)
    print(" 🚀 COMPARATIVA MULTI-AÑO (2 AÑOS): BASELINE VS INVERSIÓN INTELIGENTE POR ESTADO DEL PATRÓN")
    print("    Capital Inicial: $200.00 USD | MDD Floor: 40% | Min Bet: $0.10 USD | 7 Ruletas Oficiales")
    print("=" * 110)
    
    events = load_all_events(window_size=20)
    print(f"Total eventos sniper identificados cronológicamente: {len(events)}")
    
    modes = [
        ("baseline", "1. BASELINE (Full Kelly + Grossman-Zhou Estándar)"),
        ("modulacion_suave", "2. INVERSIÓN INTELIGENTE A (Modulación Suave 0.5x - 1.2x)"),
        ("modulacion_fuerte", "3. INVERSIÓN INTELIGENTE B (Modulación Fuerte 0.3x - 1.35x)"),
        ("filtro_exclusivo_optimo", "4. INVERSIÓN INTELIGENTE C (Modo Centinela en Degradación)")
    ]
    
    results = []
    for m_key, m_label in modes:
        res = run_simulation(events, mode=m_key, init_bankroll=200.0, mdd_floor=0.40, min_bet=0.10)
        res["label"] = m_label
        results.append(res)
        
    df_res = pd.DataFrame(results)
    
    print("\n" + "=" * 110)
    print(" 📊 TABLA COMPARATIVA DE RESULTADOS A 2 AÑOS ($200 USD INICIAL)")
    print("=" * 110)
    
    cols_show = ["label", "final_bankroll", "pnl_neto", "roi_neto", "multiplicador", "max_dd", "win_rate", "total_inv", "peak"]
    for r in results:
        print(f"\n{r['label']}:")
        print(f"  • Capital Final:      ${r['final_bankroll']:>12,.2f} USD (Pico ATH: ${r['peak']:>12,.2f})")
        print(f"  • Ganancia Neta:      +${r['pnl_neto']:>11,.2f} USD (Multiplicador: {r['multiplicador']:>6.2f}x)")
        print(f"  • Retorno (ROI):      +{r['roi_neto']:>11.2f}%")
        print(f"  • Máximo Drawdown:     {r['max_dd']:>11.2f}%")
        print(f"  • Win Rate:            {r['win_rate']:>11.2f}% ({r['aciertos']}/{r['total_jugadas']} aciertos)")
        print(f"  • Total Invertido:    ${r['total_inv']:>12,.2f} USD")
        
    print("\n" + "=" * 110)

if __name__ == "__main__":
    main()
