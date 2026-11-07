"""
Genera la gráfica comparativa de la prueba de Inversión Inteligente a 2 años.
"""

import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from test_smart_investment_models import load_data, simulate, RULETAS

signals = load_data()

# Ejecutar simulaciones guardando curvas completas
def run_with_curve(signals, model_id, init_bankroll=200.0, mdd_floor=0.40, min_bet=0.10):
    bankroll = init_bankroll
    peak = init_bankroll
    curve = []
    
    from collections import defaultdict
    time_groups = defaultdict(list)
    for s in signals:
        time_groups[s["dt"]].append(s)
        
    roi_rank = {
        "Gatazo": 1.95, "Monje Millonario": 1.76, "Guacharo Activo": 1.39,
        "Mega Animal 40": 1.31, "Ruleta Royal": 1.26, "Lotto Activo": 1.23, "La Granjita": 1.14
    }
    
    for dt in sorted(time_groups.keys()):
        active = time_groups[dt]
        peak = max(peak, bankroll)
        floor = (1.0 - mdd_floor) * peak
        cushion = max(0.0, bankroll - floor)
        gz_mult = min(1.0, max(0.0, cushion / (mdd_floor * peak))) if (mdd_floor * peak) > 0 else 1.0
        
        for ev in active:
            r_name = ev["ruleta"]
            base_f = ev["f_unit"]
            misses = ev["trigger_consec_misses"]
            
            if model_id == "baseline":
                weight = 1.0
                f_to_use = base_f
            elif model_id == "rebound_momentum":
                if 1 <= misses <= 3:
                    weight = 1.25
                elif misses == 0:
                    weight = 0.85
                else:
                    weight = 1.00
                f_to_use = base_f
            elif model_id == "priorizacion_roi":
                weight = 1.25 if r_name in ["Gatazo", "Monje Millonario", "Guacharo Activo"] else 0.85
                f_to_use = base_f
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
            else:
                cobrado = 0.0
                pnl = -total_bet
                
            bankroll = round(bankroll + pnl, 2)
            peak = max(peak, bankroll)
            cur_dd = (peak - bankroll) / peak * 100.0 if peak > 0 else 0.0
            curve.append({"dt": ev["dt"], "saldo": bankroll, "peak": peak, "dd": cur_dd})
            
    return pd.DataFrame(curve)

df_base = run_with_curve(signals, "baseline")
df_reb = run_with_curve(signals, "rebound_momentum")
df_roi = run_with_curve(signals, "priorizacion_roi")

plt.style.use('dark_background')
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), gridspec_kw={'height_ratios': [3, 1]}, sharex=True)

# Curvas de Capital
ax1.plot(df_reb['dt'], df_reb['saldo'], color='#00FFA3', linewidth=2.2, label='Inversión Inteligente: Rebound Momentum ($48,030 USD | 240.1x)')
ax1.plot(df_roi['dt'], df_roi['saldo'], color='#00BFFF', linewidth=1.8, label='Inversión Inteligente: Priorización ROI ($29,408 USD | 147.0x)')
ax1.plot(df_base['dt'], df_base['saldo'], color='#FFD700', linewidth=1.8, linestyle='--', label='Baseline Actual: Full Kelly + G-Z ($28,618 USD | 143.1x)')

ax1.set_title('Prueba Experimental (2 Años de Data): Baseline vs Inversión Inteligente por Condición Óptima\nCartera 7 Ruletas | Capital Inicial: $200.00 USD | MDD Floor: 40%', fontsize=13, fontweight='bold', pad=15)
ax1.set_ylabel('Capital ($ USD)', fontsize=12)
ax1.grid(True, linestyle='--', alpha=0.25)
ax1.legend(loc='upper left', frameon=True, facecolor='#1E1E1E')

# Anotación final Rebound Momentum
final_val = df_reb['saldo'].iloc[-1]
final_dt = df_reb['dt'].iloc[-1]
ax1.scatter([final_dt], [final_val], color='#00FFA3', s=80, zorder=5)
ax1.annotate(f'Rebound Momentum: ${final_val:,.2f} USD\n(+67.8% vs Baseline)', 
             (final_dt, final_val), 
             xytext=(-160, -35), textcoords='offset points',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='#00FFA3', alpha=0.8),
             arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', color='#00FFA3', lw=1.5),
             fontsize=9, fontweight='bold', color='black')

# Drawdowns
ax2.plot(df_reb['dt'], -df_reb['dd'], color='#00FFA3', linewidth=1, alpha=0.8, label='DD Rebound Momentum')
ax2.plot(df_base['dt'], -df_base['dd'], color='#FFD700', linewidth=1, linestyle='--', alpha=0.8, label='DD Baseline')
ax2.axhline(-40, color='#FF4444', linestyle=':', label='Límite Floor G-Z (-40%)')
ax2.set_ylabel('Drawdown (%)', fontsize=12)
ax2.set_xlabel('Fecha', fontsize=12)
ax2.grid(True, linestyle='--', alpha=0.25)
ax2.legend(loc='lower left', frameon=True, facecolor='#1E1E1E')

plt.tight_layout()

out1 = r'C:\Users\victo\nuevas_ruletas\grafica_prueba_inversion_inteligente.png'
out2 = r'C:\Users\victo\.gemini\antigravity\brain\b416ad84-eb18-4af1-a597-d96da11175e8\grafica_prueba_inversion_inteligente.png'

plt.savefig(out1, dpi=300)
plt.savefig(out2, dpi=300)
print('Grafica guardada exitosamente en:')
print(out1)
print(out2)
