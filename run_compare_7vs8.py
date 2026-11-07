import sys
from backtest_cartera_8ruletas_general import extract_events_portfolio, run_portfolio_simulation
from config import RULETAS_CONFIG

cfg_7 = {k: v for k, v in RULETAS_CONFIG.items() if v.get('active', True) and k != 'Lotto Activo RD Int'}
cfg_8 = {k: v for k, v in RULETAS_CONFIG.items() if v.get('active', True)}

events_7 = extract_events_portfolio(cfg_7)
events_8 = extract_events_portfolio(cfg_8)

start_dt_common = events_7[0]['dt']
events_8_common = [ev for ev in events_8 if ev['dt'] >= start_dt_common]

res_7_200 = run_portfolio_simulation(events_7, initial_bankroll=200.0)
res_8_200_common = run_portfolio_simulation(events_8_common, initial_bankroll=200.0)

res_7_1000 = run_portfolio_simulation(events_7, initial_bankroll=1000.0)
res_8_1000_common = run_portfolio_simulation(events_8_common, initial_bankroll=1000.0)

f7_200 = res_7_200['final_bankroll']
f8_200 = res_8_200_common['final_bankroll']
diff_200 = f8_200 - f7_200

f7_1000 = res_7_1000['final_bankroll']
f8_1000 = res_8_1000_common['final_bankroll']
diff_1000 = f8_1000 - f7_1000

print("="*105)
print("COMPARATIVA HOMOGÉNEA EXACTA (MISMO INTERVALO DE 2 AÑOS: 108 SEMANAS)")
print("="*105)
print(f"Cartera 7 ($200 Base)  : Final = ${f7_200:,.2f} USD | Mult = {f7_200/200:,.1f}x | MDD = {res_7_200['max_drawdown']*100:.2f}% | Sharpe = {res_7_200['sharpe']:.2f}")
print(f"Cartera 8 ($200 Base)  : Final = ${f8_200:,.2f} USD | Mult = {f8_200/200:,.1f}x | MDD = {res_8_200_common['max_drawdown']*100:.2f}% | Sharpe = {res_8_200_common['sharpe']:.2f}")
print(f"Ganancia Extra Generada: {diff_200:+,.2f} USD (+{diff_200/f7_200*100:+.2f}%)")

print("\n" + "-"*105)
print(f"Cartera 7 ($1,000 Base): Final = ${f7_1000:,.2f} USD | Mult = {f7_1000/1000:,.1f}x | MDD = {res_7_1000['max_drawdown']*100:.2f}% | Sharpe = {res_7_1000['sharpe']:.2f}")
print(f"Cartera 8 ($1,000 Base): Final = ${f8_1000:,.2f} USD | Mult = {f8_1000/1000:,.1f}x | MDD = {res_8_1000_common['max_drawdown']*100:.2f}% | Sharpe = {res_8_1000_common['sharpe']:.2f}")
print(f"Ganancia Extra Generada: {diff_1000:+,.2f} USD (+{diff_1000/f7_1000*100:+.2f}%)")
