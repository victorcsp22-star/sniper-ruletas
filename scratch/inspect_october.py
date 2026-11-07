import pandas as pd
import sys
sys.path.append(r"C:\Users\victo\nuevas_ruletas")
from backtest_comparativo_anomalias import extract_portfolio_events
from config import RULETAS_CONFIG

cfg = {k: v for k, v in RULETAS_CONFIG.items() if v.get("active", True)}
ev_base = extract_portfolio_events(cfg, mode="base")
ev_enh = extract_portfolio_events(cfg, mode="enhanced")

df_b = pd.DataFrame(ev_base)
df_e = pd.DataFrame(ev_enh)

oct_b = df_b[df_b['fecha'] >= '2026-10-01']
oct_e = df_e[df_e['fecha'] >= '2026-10-01']

print("OCTOBER 2026 (FULL MONTH 2026-10-01 to 2026-10-29):")
print(f"Base: {len(oct_b)} events, {oct_b['hit'].sum()} hits ({oct_b['hit'].mean()*100:.2f}%)")
print(f"Enh : {len(oct_e)} events, {oct_e['hit'].sum()} hits ({oct_e['hit'].mean()*100:.2f}%)")

# Calculate flat unit EV for October
def calc_flat_metrics(df_sub):
    total_cost = df_sub['cost_units'].sum()
    total_payout = (df_sub['hit'] * df_sub['payout']).sum()
    pnl = total_payout - total_cost
    roi = pnl / total_cost * 100
    pf = total_payout / total_cost if total_cost > 0 else 0
    return total_cost, total_payout, pnl, roi, pf

c_b, p_b, pnl_b, roi_b, pf_b = calc_flat_metrics(oct_b)
c_e, p_e, pnl_e, roi_e, pf_e = calc_flat_metrics(oct_e)

print(f"Base Flat EV: Cost={c_b}u, Return={p_b}u, Net={pnl_b}u, ROI={roi_b:.2f}%, PF={pf_b:.2f}")
print(f"Enh  Flat EV: Cost={c_e}u, Return={p_e}u, Net={pnl_e}u, ROI={roi_e:.2f}%, PF={pf_e:.2f}")
