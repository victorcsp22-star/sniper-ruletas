import os
import sys
import pandas as pd

sys.path.append(r"C:\Users\victo\nuevas_ruletas")
from backtest_comparativo_anomalias import extract_portfolio_events
from config import RULETAS_CONFIG

cfg = {k: v for k, v in RULETAS_CONFIG.items() if v.get("active", True)}
ev_base = extract_portfolio_events(cfg, mode="base")
ev_enh = extract_portfolio_events(cfg, mode="enhanced")

print(f"Base events: {len(ev_base)}")
print(f"Enhanced events: {len(ev_enh)}")
print(f"Date range Base: {ev_base[0]['fecha']} to {ev_base[-1]['fecha']}")
print(f"Date range Enh: {ev_enh[0]['fecha']} to {ev_enh[-1]['fecha']}")

hits_b = sum(1 for e in ev_base if e['hit'])
hits_e = sum(1 for e in ev_enh if e['hit'])
print(f"Hits Base: {hits_b}/{len(ev_base)} ({hits_b/len(ev_base)*100:.2f}%)")
print(f"Hits Enh: {hits_e}/{len(ev_enh)} ({hits_e/len(ev_enh)*100:.2f}%)")
