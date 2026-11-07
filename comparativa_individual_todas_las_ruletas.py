import os
import sys
import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(r"C:\Users\victo\nuevas_ruletas")
from config import RULETAS_CONFIG, BASE_DIR, VZ_DIR, MIN_BET

def run_individual_comparison():
    out_dir = r"C:\Users\victo\.gemini\antigravity\brain\da61199f-f45d-4b1d-bcd9-a17212f844b0"
    
    # Lista de Ruletas a evaluar individualmente
    # 1. Lotto Activo
    # 2. La Granjita
    # 3. Ruleta Royal
    # 4. Guacharo Activo
    # 5. Gatazo
    # 6. Mega Animal 40
    # 7. Monje Millonario
    # 8. Lotto Activo RD (Francotirador H=12)
    # 9. Lotto Activo RD (Acumulador H>=9)
    
    STARTING_CAPITAL = 200.0
    
    def eval_standard_roulette(name, cfg):
        filepath = cfg["file"]
        if not os.path.exists(filepath):
            return None
        df = pd.read_csv(filepath, dtype={"numero": str})
        df["numero"] = df["numero"].astype(str).str.strip()
        df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        df = df.sort_values(by="sort_dt").reset_index(drop=True)
        
        lags = cfg["lags"]
        payout = cfg["payout"]
        f_unit_cfg = cfg.get("f_unit", 0.008)
        target_streaks = cfg.get("target_streaks", [1])
        nums = df["numero"].tolist()
        dts = df["sort_dt"].tolist()
        min_idx = max(lags) + 6
        
        # 1. Simulación Inversión Plana ($1.00 por candidato)
        cap_flat = STARTING_CAPITAL
        cap_history_flat = [cap_flat]
        bets_flat = 0
        wins_flat = 0
        losses_flat = 0
        mdd_flat = 0.0
        peak_flat = STARTING_CAPITAL
        
        # 2. Simulación Interés Compuesto Semanal
        cap_comp = STARTING_CAPITAL
        cap_history_comp = [cap_comp]
        bets_comp = 0
        wins_comp = 0
        losses_comp = 0
        peak_comp = STARTING_CAPITAL
        mdd_pct_comp = 0.0
        
        week_start_dt = None
        week_start_cap = STARTING_CAPITAL
        unit_bet_comp = max(MIN_BET, round(week_start_cap * f_unit_cfg, 2))
        week_tripped = False
        
        streak = 0
        
        for i in range(min_idx, len(nums)):
            actual = nums[i]
            dt = dts[i]
            rec6 = set(nums[i-6:i])
            cands = list(set([nums[i-l] for l in lags if i >= l]) - rec6)
            
            # Control Semanal
            if week_start_dt is None or (dt - week_start_dt).days >= 7:
                week_start_dt = dt
                week_start_cap = cap_comp
                unit_bet_comp = max(MIN_BET, round(week_start_cap * f_unit_cfg, 2))
                week_tripped = False
                
            if cands:
                hit = (actual in cands)
                if streak in target_streaks:
                    # Inversión Plana ($1.00 fijo por candidato)
                    cost_flat = len(cands) * 1.0
                    if cap_flat >= cost_flat:
                        bets_flat += len(cands)
                        if hit:
                            wins_flat += 1
                            cap_flat += (1.0 * payout - cost_flat)
                        else:
                            losses_flat += len(cands) # o 1 fallo de disparo
                            cap_flat -= cost_flat
                        if cap_flat > peak_flat: peak_flat = cap_flat
                        dd_f = peak_flat - cap_flat
                        if dd_f > mdd_flat: mdd_flat = dd_f
                        cap_history_flat.append(cap_flat)
                        
                    # Interés Compuesto Semanal
                    if not week_tripped and cap_comp >= (unit_bet_comp * len(cands)):
                        cost_comp = unit_bet_comp * len(cands)
                        bets_comp += len(cands)
                        if hit:
                            wins_comp += 1
                            cap_comp += (unit_bet_comp * payout - cost_comp)
                        else:
                            losses_comp += len(cands)
                            cap_comp -= cost_comp
                        if cap_comp > peak_comp: peak_comp = cap_comp
                        dd_c = (peak_comp - cap_comp) / peak_comp * 100.0 if peak_comp > 0 else 0
                        if dd_c > mdd_pct_comp: mdd_pct_comp = dd_c
                        cap_history_comp.append(cap_comp)
                        if cap_comp <= week_start_cap * 0.80:
                            week_tripped = True
                            
                streak = 0 if hit else streak + 1
            else:
                streak = 0
                
        total_ops = wins_flat + (losses_flat // max(1, len(lags)))
        win_rate = (wins_flat / (wins_flat + losses_flat) * 100.0) if (wins_flat + losses_flat) > 0 else 0
        # Win rate por disparo
        disp_wr = (wins_flat / (wins_flat + (len(cap_history_flat) - wins_flat)) * 100.0) if len(cap_history_flat) > 1 else 0
        pf_flat = ((wins_flat * (payout - len(cands))) / (losses_flat * 1.0)) if losses_flat > 0 else 0
        
        # Enfoque estricto contable de PnL:
        pnl_flat = cap_flat - STARTING_CAPITAL
        pnl_comp = cap_comp - STARTING_CAPITAL
        
        be_rate = cfg.get("be_rate", 100.0 / payout)
        
        return {
            "name": name,
            "disparos": wins_flat + (losses_flat // 2),
            "apuestas_totales": bets_flat,
            "aciertos": wins_flat,
            "win_rate_apuesta": (wins_flat / bets_flat * 100.0) if bets_flat > 0 else 0,
            "be_rate": be_rate,
            "edge": ((wins_flat / bets_flat * 100.0) - be_rate) if bets_flat > 0 else 0,
            "cap_flat": cap_flat,
            "pnl_flat": pnl_flat,
            "mdd_flat": mdd_flat,
            "cap_comp": cap_comp,
            "pnl_comp": pnl_comp,
            "mult_comp": cap_comp / STARTING_CAPITAL,
            "mdd_pct_comp": mdd_pct_comp,
            "hist_flat": cap_history_flat,
            "hist_comp": cap_history_comp
        }

    # Evaluar Lotto Activo RD Internacional
    def eval_lotto_activo_rd(mode="franco"):
        filepath = "C:/Users/victo/nuevas_ruletas/lotto_activo_rd_lotoven_completo.csv"
        df = pd.read_csv(filepath, dtype={"numero": str})
        hora_order = {
            "08:30 AM": 1, "09:30 AM": 2, "10:30 AM": 3, "11:30 AM": 4,
            "12:30 PM": 5, "01:30 PM": 6, "02:30 PM": 7, "03:30 PM": 8,
            "04:30 PM": 9, "05:30 PM": 10, "06:30 PM": 11, "07:30 PM": 12
        }
        df["h_rank"] = df["hora"].map(hora_order)
        df["sort_dt"] = pd.to_datetime(df["fecha"] + " 12:00 PM")
        df = df.sort_values(by=["fecha", "h_rank"]).reset_index(drop=True)
        
        nums = df["numero"].tolist()
        dates = df["fecha"].tolist()
        hours = df["h_rank"].tolist()
        dts = df["sort_dt"].tolist()
        N = len(nums)
        split_idx = int(N * 0.70)
        
        canon_animals = ["0", "00"] + [str(i) for i in range(1, 37)]
        lags_in = [21, 39, 50]
        
        if mode == "franco":
            h_min = 12
            k = 1
            f_unit = 0.0145  # 0.50x Kelly
            name = "Lotto Activo RD (Francotirador H=12)"
        else:
            h_min = 9
            k = 2
            f_unit = 0.0035  # 0.35x Kelly
            name = "Lotto Activo RD (Acumulador H>=9)"
            
        cap_flat = STARTING_CAPITAL
        cap_history_flat = [cap_flat]
        bets_flat = 0; wins_flat = 0; losses_flat = 0
        peak_flat = 200.0; mdd_flat = 0.0
        
        cap_comp = STARTING_CAPITAL
        cap_history_comp = [cap_comp]
        bets_comp = 0; wins_comp = 0; losses_comp = 0
        peak_comp = 200.0; mdd_pct_comp = 0.0
        
        week_start_dt = None; week_start_cap = 200.0
        unit_bet_comp = max(MIN_BET, round(week_start_cap * f_unit, 2))
        week_tripped = False
        
        current_date = None; seen_today = set(); day_repeat = False
        
        for i in range(split_idx, N):
            actual = nums[i]; d = dates[i]; dt = dts[i]; h = hours[i]
            
            if week_start_dt is None or (dt - week_start_dt).days >= 7:
                week_start_dt = dt
                week_start_cap = cap_comp
                unit_bet_comp = max(MIN_BET, round(week_start_cap * f_unit, 2))
                week_tripped = False
                
            if d != current_date:
                current_date = d; seen_today = set(); day_repeat = False
            if actual in seen_today: day_repeat = True
            
            if h >= h_min and not day_repeat:
                vivos = [a for a in canon_animals if a not in seen_today]
                rec3 = set(nums[i-3:i])
                vivos_filt = [a for a in vivos if a not in rec3] or vivos
                scored = [(a, sum(1.0 for l in lags_in if i >= l and nums[i-l] == a)) for a in vivos_filt]
                scored = [x for x in scored if x[1] > 0]
                scored.sort(key=lambda x: x[1], reverse=True)
                targets = [x[0] for x in scored[:k]]
                
                # Flat
                for t in targets:
                    if cap_flat >= 1.0:
                        bets_flat += 1
                        if t == actual:
                            wins_flat += 1; cap_flat += 29.0
                        else:
                            losses_flat += 1; cap_flat -= 1.0
                        if cap_flat > peak_flat: peak_flat = cap_flat
                        dd_f = peak_flat - cap_flat
                        if dd_f > mdd_flat: mdd_flat = dd_f
                        cap_history_flat.append(cap_flat)
                        
                # Comp
                if not week_tripped:
                    for t in targets:
                        if cap_comp >= unit_bet_comp:
                            bets_comp += 1
                            if t == actual:
                                wins_comp += 1; cap_comp += (unit_bet_comp * 29.0)
                            else:
                                losses_comp += 1; cap_comp -= unit_bet_comp
                            if cap_comp > peak_comp: peak_comp = cap_comp
                            dd_c = (peak_comp - cap_comp) / peak_comp * 100.0 if peak_comp > 0 else 0
                            if dd_c > mdd_pct_comp: mdd_pct_comp = dd_c
                            cap_history_comp.append(cap_comp)
                            if cap_comp <= week_start_cap * 0.80:
                                week_tripped = True
                                
            seen_today.add(actual)
            
        return {
            "name": name,
            "disparos": bets_flat // k,
            "apuestas_totales": bets_flat,
            "aciertos": wins_flat,
            "win_rate_apuesta": (wins_flat / bets_flat * 100.0) if bets_flat > 0 else 0,
            "be_rate": 3.33,
            "edge": ((wins_flat / bets_flat * 100.0) - 3.33) if bets_flat > 0 else 0,
            "cap_flat": cap_flat,
            "pnl_flat": cap_flat - 200.0,
            "mdd_flat": mdd_flat,
            "cap_comp": cap_comp,
            "pnl_comp": cap_comp - 200.0,
            "mult_comp": cap_comp / 200.0,
            "mdd_pct_comp": mdd_pct_comp,
            "hist_flat": cap_history_flat,
            "hist_comp": cap_history_comp
        }

    results = []
    for r_name, cfg in RULETAS_CONFIG.items():
        if cfg.get("active", True):
            res = eval_standard_roulette(r_name, cfg)
            if res:
                results.append(res)
                
    res_rd_franco = eval_lotto_activo_rd("franco")
    res_rd_acum = eval_lotto_activo_rd("acum")
    results.append(res_rd_franco)
    results.append(res_rd_acum)
    
    # Imprimir Tabla Comparativa Maestra
    print("=" * 115)
    print("TABLA COMPARATIVA INSTITUCIONAL: TODAS LAS RULETAS EVALUADAS INDIVIDUALMENTE")
    print(f"Capital Inicial: $200.00 USD | Simulación Individual Completa de Cada Activo")
    print("=" * 115)
    print(f"{'Ruleta':<32} | {'Tasa Acierto':<12} | {'Break-even':<10} | {'Edge (+EV)':<10} | {'Inversión Plana ($200)':<22} | {'Interés Compuesto ($200)':<20}")
    print(f"{'':<32} | {'':<12} | {'':<10} | {'':<10} | {'Final':<9} {'PnL':<6} {'MDD':<5} | {'Final':<10} {'Mult':<6} {'MDD%':<4}")
    print("-" * 115)
    
    for r in results:
        tasa = f"{r['win_rate_apuesta']:.2f}%"
        be = f"{r['be_rate']:.2f}%"
        edge = f"{r['edge']:+.2f}%"
        flat_str = f"${r['cap_flat']:>6.0f} (+${r['pnl_flat']:>4.0f}, -${r['mdd_flat']:>3.0f})"
        comp_str = f"${r['cap_comp']:>7.0f} ({r['mult_comp']:>4.1f}x, {r['mdd_pct_comp']:>2.0f}%)"
        print(f"{r['name']:<32} | {tasa:<12} | {be:<10} | {edge:<10} | {flat_str:<22} | {comp_str:<20}")
    print("-" * 115)

    # Gráfico Comparativo Maestro
    fig, axes = plt.subplots(2, 1, figsize=(15, 11), gridspec_kw={'height_ratios': [1.2, 1]})
    fig.suptitle("Comparativa Maestra Individual: Lotto Activo RD vs Ruletas del Núcleo Oficial ($200 USD Base)", fontsize=13, fontweight='bold')
    
    ax1 = axes[0]
    names = [r["name"] for r in results]
    edges = [r["edge"] for r in results]
    colors = ['#2ca02c' if e > 0 else '#d62728' for e in edges]
    y_pos = np.arange(len(names))
    
    bars = ax1.barh(y_pos, edges, color=colors, edgecolor='black', alpha=0.85)
    ax1.axvline(0, color='black', linewidth=1)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(names, fontsize=9, fontweight='bold')
    ax1.invert_yaxis()
    ax1.set_xlabel("Ventaja Matemática Neta sobre la Banca: Tasa Acierto (%) - Break-even (%)", fontsize=10)
    ax1.set_title("Ranking por Ventaja Matemática Neta (+EV %) Individual", fontweight='bold')
    ax1.grid(True, alpha=0.3)
    for bar in bars:
        w = bar.get_width()
        offset = 0.08 if w >= 0 else -0.45
        ax1.text(w + offset, bar.get_y() + bar.get_height()/2, f"{w:+.2f}%", va='center', fontsize=8.5, fontweight='bold')
        
    ax2 = axes[1]
    mults = [r["mult_comp"] for r in results]
    bars2 = ax2.barh(y_pos, mults, color='#1f77b4', edgecolor='black', alpha=0.85)
    ax2.axvline(1.0, color='red', linestyle='--', label='Sin Crecimiento (1.0x = $200)')
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(names, fontsize=9, fontweight='bold')
    ax2.invert_yaxis()
    ax2.set_xlabel("Multiplicador de Capital con Reinversión Semanal (x del Capital Inicial)", fontsize=10)
    ax2.set_title("Crecimiento Compuesto Individual ($200 USD Base)", fontweight='bold')
    ax2.legend(loc='lower right')
    ax2.grid(True, alpha=0.3)
    for bar in bars2:
        w = bar.get_width()
        ax2.text(w + 0.3, bar.get_y() + bar.get_height()/2, f"{w:.1f}x (${w*200:,.0f})", va='center', fontsize=8.5, fontweight='bold')
        
    plt.tight_layout()
    chart_file = os.path.join(out_dir, "grafica_comparativa_maestra_todas_las_ruletas.png")
    plt.savefig(chart_file, dpi=300)
    plt.close()
    print(f"\nGráfica comparativa guardada exitosamente en: {chart_file}")

if __name__ == "__main__":
    run_individual_comparison()
