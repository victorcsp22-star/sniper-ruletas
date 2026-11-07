import os
import pandas as pd
from sim_core import RULETAS, simulate_sniper_strategy
from audit_questions_1_2_3 import load_data

core_7 = ['Lotto Activo', 'La Granjita', 'Ruleta Royal', 'Guacharo Activo', 'Gatazo', 'Mega Animal 40', 'Monje Millonario']

for r_name in core_7:
    cfg = RULETAS[r_name]
    df = load_data(cfg['file'])
    print(f"=== {r_name} (Payout: {cfg['payout']}x, Lags: {cfg['current_lags']}, Current rec_w: {cfg['rec_w']}) ===")
    use_ac = (r_name in ['Lotto Activo', 'Ruleta Royal'])
    for rw in [2, 4, 5, 6, 7, 8, 9, 10, 12]:
        res = simulate_sniper_strategy(df, cfg['current_lags'], rw, cfg['target_streaks'], use_ac, cfg['payout'])
        mark = " *ACTUAL*" if rw == cfg['rec_w'] else ""
        print(f"  rec_w={rw:2d} | Trades={res['trades']:4d} | WR={res['wr']:5.2f}% | AvgCands={res['avg_cands']:4.2f} | BE={res['be_rate']:5.2f}% | ROI={res['roi']:+6.2f}% | PnL={res['pnl']:+7.1f}{mark}")
    print()
