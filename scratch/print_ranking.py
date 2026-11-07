import pandas as pd
df = pd.read_csv(r'C:\Users\victo\nuevas_ruletas\scratch\analisis_comparativo_15ruletas.csv')
for _, r in df.sort_values(by='roi', ascending=False).iterrows():
    name = r['name']
    payout = int(r['payout'])
    wr = r['win_rate']
    roi = r['roi']
    pf = r['profit_factor']
    dd = r['max_dd']
    st = r['status']
    print(f"{name:<30} | Payout: {payout:>2}x | WR: {wr:>5.2f}% | ROI: {roi:>+6.2f}% | PF: {pf:>4.2f} | MaxDD: ${dd:>5.2f} | {st}")
