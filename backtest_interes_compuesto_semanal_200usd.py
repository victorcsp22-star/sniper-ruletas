import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def run_weekly_compounding_backtest():
    csv_file = "C:/Users/victo/nuevas_ruletas/lotto_activo_rd_lotoven_completo.csv"
    out_dir = "C:/Users/victo/.gemini/antigravity/brain/da61199f-f45d-4b1d-bcd9-a17212f844b0"
    
    df = pd.read_csv(csv_file, dtype={"numero": str})
    hora_order = {
        "08:30 AM": 1, "09:30 AM": 2, "10:30 AM": 3, "11:30 AM": 4,
        "12:30 PM": 5, "01:30 PM": 6, "02:30 PM": 7, "03:30 PM": 8,
        "04:30 PM": 9, "05:30 PM": 10, "06:30 PM": 11, "07:30 PM": 12
    }
    df["h_rank"] = df["hora"].map(hora_order)
    df["dt"] = pd.to_datetime(df["fecha"])
    df = df.sort_values(by=["fecha", "h_rank"]).reset_index(drop=True)
    
    nums = df["numero"].tolist()
    dates = df["fecha"].tolist()
    hours = df["h_rank"].tolist()
    dts = df["dt"].tolist()
    N = len(nums)
    
    canon_animals = [
        "0", "00", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
        "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
        "21", "22", "23", "24", "25", "26", "27", "28", "29", "30",
        "31", "32", "33", "34", "35", "36"
    ]
    lags_in = [21, 39, 50]
    
    # 70% In-Sample / 30% Out-of-Sample
    split_idx = int(N * 0.70)
    
    # Simulación con Interés Compuesto y Reinversión Semanal (Step-Compounding 7 días)
    # Parámetros:
    # Capital Inicial: $200.00 USD
    # Ciclo de reinversión: cada 7 días naturales
    # Circuit Breaker semanal: si pierde más del 20% en la misma semana, pausa hasta el siguiente ciclo
    
    STARTING_CAPITAL = 200.0
    MIN_BET = 0.10
    
    def simulate_compounding(h_min, k, only_clean, p_empirico, kelly_mult=0.75):
        # Kelly teórico: f* = (30*p - 1) / 29
        f_star = (30.0 * p_empirico - 1.0) / 29.0
        f_active = f_star * kelly_mult
        
        bankroll = STARTING_CAPITAL
        history = [bankroll]
        
        current_date = None
        seen_today = set()
        day_repeat = False
        
        # Control Semanal
        week_start_date = None
        week_start_bankroll = STARTING_CAPITAL
        unit_bet = max(MIN_BET, round(week_start_bankroll * f_active, 2))
        week_circuit_tripped = False
        
        bets = 0
        wins = 0
        losses = 0
        total_vol = 0.0
        
        weekly_balances = []
        
        for i in range(split_idx, N):
            actual = nums[i]
            d = dates[i]
            dt = dts[i]
            h = hours[i]
            
            # Inicialización o reinicio de ciclo semanal (cada 7 días)
            if week_start_date is None:
                week_start_date = dt
                week_start_bankroll = bankroll
                unit_bet = max(MIN_BET, round(week_start_bankroll * f_active, 2))
                week_circuit_tripped = False
            elif (dt - week_start_date).days >= 7:
                weekly_balances.append({
                    "week_start": week_start_date,
                    "bankroll": bankroll,
                    "unit_bet": unit_bet
                })
                week_start_date = dt
                week_start_bankroll = bankroll
                unit_bet = max(MIN_BET, round(week_start_bankroll * f_active, 2))
                week_circuit_tripped = False
                
            # Control diario
            if d != current_date:
                current_date = d
                seen_today = set()
                day_repeat = False
                
            if actual in seen_today:
                day_repeat = True
                
            operate = (h >= h_min)
            if only_clean and day_repeat:
                operate = False
            if week_circuit_tripped:
                operate = False
                
            if operate:
                vivos = [a for a in canon_animals if a not in seen_today]
                rec3 = set(nums[i-3:i])
                vivos_filt = [a for a in vivos if a not in rec3]
                if not vivos_filt: vivos_filt = vivos
                
                scored = []
                for a in vivos_filt:
                    sc = sum(1.0 for l in lags_in if i >= l and nums[i-l] == a)
                    if sc > 0:
                        scored.append((a, sc))
                scored.sort(key=lambda x: x[1], reverse=True)
                targets = [item[0] for item in scored[:k]]
                
                for t in targets:
                    if bankroll < unit_bet:
                        break
                    bets += 1
                    total_vol += unit_bet
                    if t == actual:
                        wins += 1
                        bankroll += (unit_bet * 29.0)
                    else:
                        losses += 1
                        bankroll -= unit_bet
                    history.append(bankroll)
                    
                    # Verificación de Circuit Breaker semanal (-20% respecto al inicio de semana)
                    if bankroll <= week_start_bankroll * 0.80:
                        week_circuit_tripped = True
                        
            seen_today.add(actual)
            
        arr = np.array(history)
        peaks = np.maximum.accumulate(arr)
        dds = (peaks - arr) / peaks * 100.0
        mdd_pct = np.max(dds) if len(dds) > 0 else 0.0
        mdd_dollars = np.max(peaks - arr) if len(peaks) > 0 else 0.0
        
        win_rate = (wins / bets * 100.0) if bets > 0 else 0.0
        pf = (wins * 29.0) / losses if losses > 0 else 0.0
        net = bankroll - STARTING_CAPITAL
        roi_cap = (net / STARTING_CAPITAL) * 100.0
        roi_vol = (net / total_vol) * 100.0 if total_vol > 0 else 0.0
        
        return {
            "h_min": h_min,
            "k": k,
            "f_active": f_active,
            "final_bankroll": bankroll,
            "net": net,
            "roi_cap": roi_cap,
            "roi_vol": roi_vol,
            "bets": bets,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "pf": pf,
            "mdd_pct": mdd_pct,
            "mdd_dollars": mdd_dollars,
            "history": history,
            "weekly_balances": weekly_balances
        }

    # Probar los 3 Perfiles Óptimos con Reinversión Semanal
    # 1. Francotirador: H=12, k=1, Día Limpio (p=0.0614, Kelly f* = 2.90%)
    res_franco_075 = simulate_compounding(12, 1, True, 0.0614, kelly_mult=0.75)
    res_franco_050 = simulate_compounding(12, 1, True, 0.0614, kelly_mult=0.50)
    
    # 2. Equilibrado: H>=11, k=2, Día Limpio (p=0.0434, Kelly f* = 1.04%)
    res_equil_075 = simulate_compounding(11, 2, True, 0.0434, kelly_mult=0.75)
    res_equil_050 = simulate_compounding(11, 2, True, 0.0434, kelly_mult=0.50)
    
    # 3. Acumulador: H>=9, k=2, Día Limpio (p=0.0422, Kelly f* = 0.92%)
    res_acum_050  = simulate_compounding(9, 2, True, 0.0422, kelly_mult=0.50)
    res_acum_035  = simulate_compounding(9, 2, True, 0.0422, kelly_mult=0.35)

    print("="*95)
    print("BACKTEST: INTERÉS COMPUESTO Y REINVERSIÓN SEMANAL (7 DÍAS) | CAPITAL INICIAL: $200 USD")
    print("Muestra Fuera de Muestra (OOS): 5,789 sorteos (2025-06 a 2026-10, ~1.3 años)")
    print("="*95)
    
    configs = [
        ("Perfil Francotirador (H=12, k=1) | 0.75x Kelly (2.17%/apuesta)", res_franco_075),
        ("Perfil Francotirador (H=12, k=1) | 0.50x Kelly (1.45%/apuesta)", res_franco_050),
        ("Perfil Equilibrado   (H>=11, k=2) | 0.75x Kelly (0.78%/apuesta)", res_equil_075),
        ("Perfil Equilibrado   (H>=11, k=2) | 0.50x Kelly (0.52%/apuesta)", res_equil_050),
        ("Perfil Acumulador    (H>=9, k=2) | 0.50x Kelly (0.46%/apuesta)", res_acum_050),
        ("Perfil Acumulador    (H>=9, k=2) | 0.35x Kelly (0.32%/apuesta)", res_acum_035),
    ]
    
    for name, r in configs:
        print(f"\n>>> {name}")
        print(f"  Capital Inicial:     ${STARTING_CAPITAL:.2f} USD")
        print(f"  Capital Final:       ${r['final_bankroll']:,.2f} USD (+${r['net']:,.2f} USD)")
        print(f"  Multiplicador Cuenta:{r['final_bankroll']/STARTING_CAPITAL:.2f}x de crecimiento")
        print(f"  Rentabilidad / Cap:  {r['roi_cap']:+,.2f}%")
        print(f"  Total Disparos:      {r['bets']} (Aciertos: {r['wins']}, Fallos: {r['losses']})")
        print(f"  Tasa de Acierto:     {r['win_rate']:.3f}% (Break-even necesario: 3.333%)")
        print(f"  Profit Factor:       {r['pf']:.2f}")
        print(f"  Max Drawdown (%):    {r['mdd_pct']:.2f}% del pico")
        print(f"  Max Drawdown ($):    ${r['mdd_dollars']:,.2f} USD")

    # Gráfico Institucional
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [2.2, 1]})
    fig.suptitle("Interés Compuesto y Reinversión Semanal (Step-Compounding 7 Días | $200 USD Base)\nLotto Activo RD Internacional - Validación Ciega Out-of-Sample (5,789 Sorteos)", fontsize=13, fontweight='bold')
    
    ax1 = axes[0]
    ax1.plot(res_acum_050["history"], label=f'Acumulador (H>=9, 0.50x Kelly): ${res_acum_050["final_bankroll"]:,.2f} ({res_acum_050["final_bankroll"]/200:.1f}x, MDD={res_acum_050["mdd_pct"]:.1f}%)', color='#2ca02c', linewidth=2.2)
    ax1.plot(res_equil_075["history"], label=f'Equilibrado (H>=11, 0.75x Kelly): ${res_equil_075["final_bankroll"]:,.2f} ({res_equil_075["final_bankroll"]/200:.1f}x, MDD={res_equil_075["mdd_pct"]:.1f}%)', color='#1f77b4', linewidth=2.0)
    ax1.plot(res_franco_075["history"], label=f'Francotirador (H=12, 0.75x Kelly): ${res_franco_075["final_bankroll"]:,.2f} ({res_franco_075["final_bankroll"]/200:.1f}x, MDD={res_franco_075["mdd_pct"]:.1f}%)', color='#ff7f0e', linewidth=1.8)
    ax1.plot(res_acum_035["history"], label=f'Acumulador Conservador (0.35x Kelly): ${res_acum_035["final_bankroll"]:,.2f} ({res_acum_035["final_bankroll"]/200:.1f}x, MDD={res_acum_035["mdd_pct"]:.1f}%)', color='#9467bd', linewidth=1.8)
    
    ax1.axhline(STARTING_CAPITAL, color='black', linestyle=':', label='Capital Inicial ($200.00 USD)')
    ax1.set_title("Curva de Crecimiento de Capital con Interés Compuesto Semanal ($ USD)", fontweight='bold')
    ax1.set_ylabel("Capital ($ USD)")
    ax1.set_yscale("log") # Escala logarítmica para ver la progresión compuesta
    ax1.legend(loc='upper left', fontsize=9.2)
    ax1.grid(True, alpha=0.3, which='both')
    
    ax2 = axes[1]
    for r, lbl, col in [
        (res_acum_050, 'Acumulador 0.50x Kelly', '#2ca02c'),
        (res_equil_075, 'Equilibrado 0.75x Kelly', '#1f77b4'),
        (res_franco_075, 'Francotirador 0.75x Kelly', '#ff7f0e')
    ]:
        arr = np.array(r["history"])
        pk = np.maximum.accumulate(arr)
        dd = (pk - arr) / pk * 100.0
        ax2.plot(dd, label=f'{lbl} (Max: {r["mdd_pct"]:.1f}%)', color=col, linewidth=1.3)
    ax2.set_title("Porcentaje de Drawdown en Tiempo Real (% del Pico)", fontweight='bold')
    ax2.set_xlabel("Número de Disparos")
    ax2.set_ylabel("Drawdown (%)")
    ax2.legend(loc='upper right', fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    chart_out = os.path.join(out_dir, "grafica_interes_compuesto_semanal_200usd.png")
    plt.savefig(chart_out, dpi=300)
    plt.close()
    print(f"\nGráfica de interés compuesto guardada en: {chart_out}")

if __name__ == "__main__":
    run_weekly_compounding_backtest()
