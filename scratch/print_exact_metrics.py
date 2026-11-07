import json

with open("audit_results.json", "r", encoding="utf-8") as f:
    d = json.load(f)

print("="*70)
print("EXTRACCIÓN DE AUDITORÍA: ESTRATEGIA MAXIMIZADA")
print("="*70)
for k, v in d["strategies"].items():
    print(f"\n--- Estrategia: {k} ---")
    print(f"Capital Final:         ${v.get('final_bankroll', 0):,.2f} USD")
    print(f"ATH Peak Máximo:       ${v.get('peak_bankroll', 0):,.2f} USD")
    print(f"Ganancia Neta (PnL):   ${v.get('total_pnl', 0):,.2f} USD")
    print(f"Retorno Total:         {v.get('total_return_pct', 0):,.2f}%")
    print(f"Tasa Geométrica Semanal: {v.get('weekly_cagr_pct', 0):.2f}% semanal")
    print(f"Máximo Drawdown (MDD): {v.get('max_drawdown_pct', 0):.2f}%")
    print(f"Total Disparos:        {v.get('total_bets', 0)} ({v.get('wins', 0)} Wins / {v.get('losses', 0)} Losses)")
    print(f"Win Rate:              {v.get('win_rate_pct', 0):.2f}%")
    print(f"Profit Factor:         {v.get('profit_factor', 0):.2f}")
    print(f"Sharpe Ratio:          {v.get('sharpe_annualized', 0):.2f}")
    print(f"Sortino Ratio:         {v.get('sortino_annualized', 0):.2f}")
    print(f"Expectancy por Tiro:   ${v.get('expectancy_per_bet', 0):,.2f} USD")

print("\n--- Monte Carlo (1,000 Iteraciones) ---")
mc = d.get("monte_carlo", {}).get("optimized_max", {})
print(f"Capital Final Mediano: ${mc.get('median_final_bankroll', 0):,.2f} USD")
print(f"Percentil 5 (Peor 5%): ${mc.get('p5_final_bankroll', 0):,.2f} USD")
print(f"Percentil 95 (Mejor 5%): ${mc.get('p95_final_bankroll', 0):,.2f} USD")
print(f"Worst-Case DD (95% Conf): {mc.get('worst_case_drawdown_95_pct', 0):.2f}%")
print(f"Worst-Case DD (99% Conf): {mc.get('worst_case_drawdown_99_pct', 0):.2f}%")
print(f"Prob. Preservar > $200:   {mc.get('prob_capital_preservation_pct', 0):.2f}%")
print("="*70)
