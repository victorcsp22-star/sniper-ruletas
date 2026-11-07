import os
import sys
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(r"C:\Users\victo\nuevas_ruletas")
from config import (
    RULETAS_CONFIG, MIN_BET,
    SMART_INVESTMENT_ENABLED, REBOUND_BOOST_MULTIPLIER,
    FATIGUE_DISCOUNT_MULTIPLIER, NEUTRAL_MULTIPLIER
)

CONFIG_7 = {k: v for k, v in RULETAS_CONFIG.items() if v.get("active", True)}
OUTPUT_DIR = r"C:\Users\victo\.gemini\antigravity\brain\da61199f-f45d-4b1d-bcd9-a17212f844b0"

def extract_all_events():
    all_events = []
    for r_name, cfg in CONFIG_7.items():
        if not os.path.exists(cfg["file"]):
            print(f"Advertencia: No existe {cfg['file']}")
            continue
        df = pd.read_csv(cfg["file"], dtype={"numero": str})
        df["numero"] = df["numero"].astype(str).str.strip()
        df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        df = df.sort_values(by="sort_dt").reset_index(drop=True)

        lags = cfg["lags"]
        payout = cfg["payout"]
        f_unit = cfg["f_unit"]
        target_streaks = cfg.get("target_streaks", [1])
        nums = df["numero"].tolist()
        min_idx = max(lags) + 6

        streak = 0
        trigger_misses = 0
        for i in range(min_idx, len(nums)):
            actual = nums[i]
            rec6 = set(nums[i-6:i])
            cands = list(set([nums[i-l] for l in lags]) - rec6)
            if cands:
                hit = (actual in cands)
                if streak in target_streaks:
                    all_events.append({
                        "dt": df.iloc[i]["sort_dt"],
                        "fecha": df.iloc[i]["fecha"],
                        "hora": df.iloc[i]["hora"],
                        "ruleta": r_name,
                        "cost_units": len(cands),
                        "hit": hit,
                        "payout": payout,
                        "f_unit": f_unit,
                        "trigger_misses": trigger_misses
                    })
                    trigger_misses = 0 if hit else trigger_misses + 1
                streak = 0 if hit else streak + 1
            else:
                streak = 0

    df_events = pd.DataFrame(all_events)
    df_events = df_events.sort_values(by="dt").reset_index(drop=True)
    return df_events

def run_simulation(df_events, initial_bankroll=200.0, mode="kelly_flat_smart", flat_amount=1.0):
    """
    Modes:
      - 'kelly_flat_smart': Bet = 200 * f_unit * 0.75 * Smart Multiplier (plana basada en $200)
      - 'kelly_flat_plain': Bet = 200 * f_unit * 0.75 (sin Smart)
      - 'fixed_dollar_smart': Bet = flat_amount * Smart Multiplier
      - 'fixed_dollar_plain': Bet = flat_amount
    """
    bankroll = initial_bankroll
    bankroll_history = [bankroll]
    bet_history = []
    
    total_bets_cost = 0.0
    wins = 0
    losses = 0
    gross_profit = 0.0
    gross_loss = 0.0
    
    current_w_streak = 0
    current_l_streak = 0
    max_w_streak = 0
    max_l_streak = 0
    
    ruined = False
    ruin_idx = None

    for idx, row in df_events.iterrows():
        f_unit = row["f_unit"]
        cost_units = row["cost_units"]
        hit = row["hit"]
        payout = row["payout"]
        t_misses = row["trigger_misses"]
        
        # Factor Smart
        if "smart" in mode:
            if t_misses in [1, 2, 3]:
                mult = REBOUND_BOOST_MULTIPLIER   # 1.25
            elif t_misses == 0:
                mult = FATIGUE_DISCOUNT_MULTIPLIER # 0.85
            else:
                mult = NEUTRAL_MULTIPLIER          # 1.00
        else:
            mult = 1.0

        if "kelly" in mode:
            # Tamaño plano derivado de $200 de capital base (0.75x Kelly)
            unit_bet = max(MIN_BET, round(initial_bankroll * f_unit * 0.75 * mult, 2))
        else:
            unit_bet = max(MIN_BET, round(flat_amount * mult, 2))
            
        bet_cost = unit_bet * cost_units
        
        if bankroll < bet_cost:
            ruined = True
            if ruin_idx is None:
                ruin_idx = idx
            # Si no alcanza, apuesta lo que queda o se declara ruina
            break
            
        total_bets_cost += bet_cost
        
        if hit:
            win_amount = (unit_bet * payout) - bet_cost
            bankroll += win_amount
            gross_profit += win_amount
            wins += 1
            current_w_streak += 1
            current_l_streak = 0
            if current_w_streak > max_w_streak: max_w_streak = current_w_streak
        else:
            bankroll -= bet_cost
            gross_loss += bet_cost
            losses += 1
            current_l_streak += 1
            current_w_streak = 0
            if current_l_streak > max_l_streak: max_l_streak = current_l_streak
            
        bankroll_history.append(bankroll)
        bet_history.append({
            "dt": row["dt"],
            "fecha": row["fecha"],
            "ruleta": row["ruleta"],
            "cost": bet_cost,
            "hit": hit,
            "bankroll": bankroll
        })

    arr = np.array(bankroll_history)
    peaks = np.maximum.accumulate(arr)
    dds = peaks - arr
    mdd_dollars = np.max(dds)
    mdd_pct = (mdd_dollars / np.max(peaks)) * 100.0 if np.max(peaks) > 0 else 0
    
    total_ops = wins + losses
    win_rate = (wins / total_ops * 100.0) if total_ops > 0 else 0
    pf = (gross_profit / gross_loss) if gross_loss > 0 else 0
    net_pnl = bankroll - initial_bankroll
    roi_vol = (net_pnl / total_bets_cost * 100.0) if total_bets_cost > 0 else 0
    roi_cap = (net_pnl / initial_bankroll * 100.0)
    
    return {
        "mode": mode,
        "bankroll_history": bankroll_history,
        "df_bets": pd.DataFrame(bet_history),
        "final_bankroll": bankroll,
        "net_pnl": net_pnl,
        "total_volume": total_bets_cost,
        "total_ops": total_ops,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "pf": pf,
        "roi_vol": roi_vol,
        "roi_cap": roi_cap,
        "mdd_dollars": mdd_dollars,
        "mdd_pct": mdd_pct,
        "max_w_streak": max_w_streak,
        "max_l_streak": max_l_streak,
        "ruined": ruined,
        "ruin_idx": ruin_idx
    }

def main():
    print("=" * 80)
    print("BACKTEST INSTITUCIONAL: CARTERA 7 RULETAS CON INVERSIÓN PLANA ($200 USD)")
    print("Estrategia Oficial: Gatillo Sniper Post-Fallo 1 + Smart Investment")
    print("=" * 80)
    
    df_events = extract_all_events()
    min_date = df_events["fecha"].min()
    max_date = df_events["fecha"].max()
    print(f"Total Disparos Registrados en Cartera 7: {len(df_events)} eventos")
    print(f"Período Temporal: {min_date} a {max_date} (~2 años completos)\n")
    
    # 4 Configuraciones de Inversión Plana
    # 1. Base Kelly Plana + Smart Investment (Apuesta óptima fija derivada de $200)
    # 2. Base Kelly Plana Pura (Sin Smart)
    # 3. $1.00 USD Fijo por Animalito + Smart
    # 4. $0.50 USD Fijo por Animalito + Smart
    
    res1 = run_simulation(df_events, initial_bankroll=200.0, mode="kelly_flat_smart")
    res2 = run_simulation(df_events, initial_bankroll=200.0, mode="kelly_flat_plain")
    res3 = run_simulation(df_events, initial_bankroll=200.0, mode="fixed_dollar_smart", flat_amount=1.0)
    res4 = run_simulation(df_events, initial_bankroll=200.0, mode="fixed_dollar_smart", flat_amount=0.50)
    
    configs = [
        ("Modelo 1: Kelly Base Fijo ($200) + Smart Rebound (Oficial)", res1),
        ("Modelo 2: Kelly Base Fijo ($200) Puro (Sin Smart)", res2),
        ("Modelo 3: $1.00 USD Fijo por Animalito + Smart Rebound", res3),
        ("Modelo 4: $0.50 USD Fijo por Animalito + Smart Rebound (Bajo Riesgo)", res4),
    ]
    
    for name, r in configs:
        print(f">>> {name}")
        print(f"  Capital Inicial:   $200.00 USD")
        print(f"  Capital Final:     ${r['final_bankroll']:,.2f} USD ({r['net_pnl']:+,.2f} USD)")
        print(f"  Rentabilidad / Cap:{r['roi_cap']:+,.2f}% sobre capital inicial")
        print(f"  ROI s/ Volumen:    {r['roi_vol']:+,.2f}% (Volumen total: ${r['total_volume']:,.2f} USD)")
        print(f"  Total Disparos:    {r['total_ops']} (Aciertos: {r['wins']}, Fallos: {r['losses']})")
        print(f"  Tasa de Acierto:   {r['win_rate']:.2f}%")
        print(f"  Profit Factor:     {r['pf']:.2f}")
        print(f"  Max Drawdown:      ${r['mdd_dollars']:,.2f} USD ({r['mdd_pct']:.2f}% del pico)")
        print(f"  Rachas Extremas:   Max Win = {r['max_w_streak']} | Max Loss = {r['max_l_streak']}")
        print(f"  ¿Riesgo de Ruina?  {'SÍ (Quebró)' if r['ruined'] else 'NO (Supervivencia 100%)'}\n")
        
    # Desglose Anual / Semestral para Modelo Oficial
    df_bets = res1["df_bets"]
    df_bets["año_mes"] = pd.to_datetime(df_bets["fecha"]).dt.to_period("M")
    
    # Gráfica Institucional
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [2.2, 1]})
    fig.suptitle("Backtest Cartera 7 Ruletas: Inversión Plana ($200 USD Capital Inicial)\nEstrategia Gatillo Sniper Post-Fallo 1 + Smart Rebound Momentum (2 Años Históricos)", fontsize=13, fontweight='bold')
    
    ax1 = axes[0]
    ax1.plot(res1["bankroll_history"], label=f'Kelly Fijo ($200) + Smart: ${res1["final_bankroll"]:,.2f} (+{res1["roi_cap"]:.1f}%, PF={res1["pf"]:.2f})', color='#2ca02c', linewidth=2.2)
    ax1.plot(res2["bankroll_history"], label=f'Kelly Fijo Puro: ${res2["final_bankroll"]:,.2f} (+{res2["roi_cap"]:.1f}%, PF={res2["pf"]:.2f})', color='#1f77b4', linewidth=1.8)
    ax1.plot(res3["bankroll_history"], label=f'$1.00 USD Fijo: ${res3["final_bankroll"]:,.2f} (+{res3["roi_cap"]:.1f}%, PF={res3["pf"]:.2f})', color='#ff7f0e', linewidth=1.8)
    ax1.plot(res4["bankroll_history"], label=f'$0.50 USD Fijo: ${res4["final_bankroll"]:,.2f} (+{res4["roi_cap"]:.1f}%, PF={res4["pf"]:.2f})', color='#9467bd', linewidth=1.8)
    
    ax1.axhline(200.0, color='black', linestyle=':', label='Capital Inicial ($200.00 USD)')
    ax1.set_title("Curva de Evolución de Capital ($ USD)", fontweight='bold')
    ax1.set_ylabel("Capital ($ USD)")
    ax1.legend(loc='upper left', fontsize=9.5)
    ax1.grid(True, alpha=0.3)
    
    # Subplot 2: Drawdown en Dólares
    ax2 = axes[1]
    for r, label, col in [
        (res1, "Drawdown Kelly Fijo + Smart", "#2ca02c"),
        (res3, "Drawdown $1.00 Fijo", "#ff7f0e"),
        (res4, "Drawdown $0.50 Fijo", "#9467bd")
    ]:
        arr = np.array(r["bankroll_history"])
        pk = np.maximum.accumulate(arr)
        dd = pk - arr
        ax2.plot(dd, label=f'{label} (Max: -${r["mdd_dollars"]:,.2f})', color=col, linewidth=1.3)
        
    ax2.set_title("Profundidad de Drawdown en Dólares ($ USD)", fontweight='bold')
    ax2.set_xlabel("Número de Disparos Ejecutados")
    ax2.set_ylabel("Drawdown ($ USD)")
    ax2.legend(loc='upper right', fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    chart_path = os.path.join(OUTPUT_DIR, "grafica_backtest_7ruletas_inversion_plana_200usd.png")
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"Gráfica institucional guardada en: {chart_path}")

if __name__ == "__main__":
    main()
