import os
import pandas as pd
from sim_core import RULETAS, simulate_sniper_strategy
from audit_questions_1_2_3 import load_data

for r_name in ['Lotto Activo', 'La Granjita', 'Ruleta Royal']:
    cfg = RULETAS[r_name]
    df = load_data(cfg['file'])
    print(f"=== {r_name} ===")
    tests = {
        'Lotto Activo': [
            ('Actual [20, 18, 14]', [20, 18, 14]),
            ('Top-3 Z [20, 18, 19]', [20, 18, 19]),
            ('Top-2 Z [20, 18]', [20, 18]),
            ('Cuarteto [20, 18, 19, 14]', [20, 18, 19, 14])
        ],
        'La Granjita': [
            ('Actual [15, 17]', [15, 17]),
            ('Top-3 Z [15, 14, 17]', [15, 14, 17]),
            ('Top-2 Z [15, 14]', [15, 14]),
            ('Alternativo [15, 14, 41]', [15, 14, 41])
        ],
        'Ruleta Royal': [
            ('Actual [16, 19, 31]', [16, 19, 31]),
            ('Top-2 Z [19, 16]', [19, 16]),
            ('Top-4 Z [19, 16, 31, 33]', [19, 16, 31, 33])
        ]
    }[r_name]
    use_ac = True
    for lbl, lags in tests:
        res = simulate_sniper_strategy(df, lags, cfg['rec_w'], cfg['target_streaks'], use_ac, cfg['payout'])
        print(f"  {lbl:<26} | Trades={res['trades']:4d} | WR={res['wr']:5.2f}% | AvgCands={res['avg_cands']:4.2f} | ROI={res['roi']:+6.2f}% | PnL={res['pnl']:+6.1f}")
