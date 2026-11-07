import json

with open(r"C:\Users\victo\nuevas_ruletas\scratch\weekly_backtest_1y.json", "r", encoding="utf-8") as f:
    data = json.load(f)

last52 = data["last_52w_of_2y"]
print(f"Last 52 of 2Y: Start ${last52[0]['bankroll_start']:,.2f} -> End ${last52[-1]['bankroll_end']:,.2f}")
total_inv = sum(w['invested'] for w in last52)
total_col = sum(w['collected'] for w in last52)
print(f"Total invested: ${total_inv:,.2f}, Collected: ${total_col:,.2f}, Net PnL: ${total_col - total_inv:,.2f}")
print(f"Wins: {sum(w['wins'] for w in last52)}, Bets: {sum(w['bets'] for w in last52)}")
