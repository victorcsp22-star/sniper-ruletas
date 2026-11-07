import json

with open(r"C:\Users\victo\nuevas_ruletas\scratch\weekly_backtest_1y.json", "r", encoding="utf-8") as f:
    data = json.load(f)

fresh = data["fresh_1y"]
total_bets = sum(w["bets"] for w in fresh)
total_wins = sum(w["wins"] for w in fresh)
total_inv = sum(w["invested"] for w in fresh)
total_col = sum(w["collected"] for w in fresh)
net_pnl = sum(w["pnl"] for w in fresh)
pos_weeks = sum(1 for w in fresh if w["pnl"] > 0)
neg_weeks = sum(1 for w in fresh if w["pnl"] < 0)

print(f"Total Bets: {total_bets}, Wins: {total_wins}, WR: {total_wins/total_bets*100:.2f}%")
print(f"Total Invested: ${total_inv:,.2f}, Collected: ${total_col:,.2f}, Net PnL: ${net_pnl:,.2f}")
print(f"Winning weeks: {pos_weeks} / {len(fresh)} ({pos_weeks/len(fresh)*100:.1f}%), Losing weeks: {neg_weeks}")

print("\n--- Todas las Semanas (1 Año Fresco: $200 USD Base) ---")
for w in fresh:
    print(f"Semana {w['week_num']:02d} ({w['start_date']} al {w['end_date']}): Inicial ${w['bankroll_start']:>10.2f} | Final ${w['bankroll_end']:>10.2f} | Disparos: {w['bets']:>2} | Aciertos: {w['wins']:>2} ({w['win_rate']:>5.1f}%) | PnL: ${w['pnl']:>9.2f} ({w['return_pct']:>+6.1f}%) | DD: {w['drawdown_pct']:>4.1f}%")
