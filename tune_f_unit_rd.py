from backtest_cartera_8ruletas_general import extract_events_portfolio, run_portfolio_simulation
from config import RULETAS_CONFIG

cfg_7 = {k: v for k, v in RULETAS_CONFIG.items() if v.get('active', True) and k != 'Lotto Activo RD Int'}
events_7 = extract_events_portfolio(cfg_7)
start_dt_common = events_7[0]['dt']
res_7 = run_portfolio_simulation(events_7, initial_bankroll=200.0)

print(f"Cartera 7 Benchmark : Final = ${res_7['final_bankroll']:>12,.2f} USD | MDD = {res_7['max_drawdown']*100:.2f}% | Sharpe = {res_7['sharpe']:.2f}")

for f_test in [0.002, 0.003, 0.004, 0.005, 0.006]:
    cfg_8 = {k: dict(v) for k, v in RULETAS_CONFIG.items() if v.get('active', True)}
    cfg_8['Lotto Activo RD Int']['f_unit'] = f_test
    events_8 = extract_events_portfolio(cfg_8)
    events_8_common = [ev for ev in events_8 if ev['dt'] >= start_dt_common]
    res_8 = run_portfolio_simulation(events_8_common, initial_bankroll=200.0)
    print(f"RD f_unit={f_test:.4f}     : Final = ${res_8['final_bankroll']:>12,.2f} USD | MDD = {res_8['max_drawdown']*100:.2f}% | Sharpe = {res_8['sharpe']:.2f}")
