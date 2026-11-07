from backtest_cartera_8ruletas_general import extract_events_portfolio, run_portfolio_simulation
from config import RULETAS_CONFIG

cfg_8_franco = {k: dict(v) for k, v in RULETAS_CONFIG.items() if v.get('active', True)}
cfg_8_franco['Lotto Activo RD Int']['min_hour'] = 12
cfg_8_franco['Lotto Activo RD Int']['f_unit'] = 0.0090 # sizing conservador para no canibalizar circuit breaker

events_7 = extract_events_portfolio({k: v for k, v in RULETAS_CONFIG.items() if v.get('active', True) and k != 'Lotto Activo RD Int'})
events_8 = extract_events_portfolio(cfg_8_franco)

start_dt_common = events_7[0]['dt']
events_8_common = [ev for ev in events_8 if ev['dt'] >= start_dt_common]

res_7 = run_portfolio_simulation(events_7, initial_bankroll=200.0)
res_8 = run_portfolio_simulation(events_8_common, initial_bankroll=200.0)

f7 = res_7['final_bankroll']
f8 = res_8['final_bankroll']

print("="*95)
print("COMPARATIVA DE CARTERA: IMPACTO DEL PERFIL FRANCOTIRADOR (H=12)")
print("="*95)
print(f"Cartera 7 (Sin RD)        : Final = ${f7:,.2f} USD | MDD = {res_7['max_drawdown']*100:.2f}% | Sharpe = {res_7['sharpe']:.2f}")
print(f"Cartera 8 (Con RD Franco) : Final = ${f8:,.2f} USD | MDD = {res_8['max_drawdown']*100:.2f}% | Sharpe = {res_8['sharpe']:.2f}")
print(f"Diferencia Neta           : {f8 - f7:+,.2f} USD")
