import json

with open("portfolio_optimization_audit.json", "r", encoding="utf-8") as f:
    d = json.load(f)

print("="*80)
print("OPTIMIZACIÓN DE CARTERA Y RIESGO - RESULTADOS EXTRAÍDOS")
print("="*80)
print(f"Multiplicador Óptimo Teórico k*: {d['optimization']['optimal_k']}x Kelly")
print("\nModelos Deterministas:")
for r in d['deterministic_results']:
    print(f"• {r['name']:<35s} | CAGR: {r['cagr_projected_annual']:>8.1f}% | MDD: {r['max_dd_pct']:>5.2f}% | Sharpe: {r['sharpe_annualized']:>5.2f} | Saldo Final: ${r['final_bankroll']:>8.2f}")

print("\nModelos Monte Carlo (10,000 caminos):")
for m in d['monte_carlo_results']:
    print(f"• {m['model_name']:<35s} | CAGR Med: {m['cagr_median']:>7.1f}% | MDD 95th: {m['max_dd_95th_percentile']:>5.2f}% | P(MDD>10%): {m['prob_breach_10pct_dd']:>5.2f}% | Sharpe: {m['sharpe_median']:>4.2f}")

print("\nMatriz de Correlación entre Ruletas:")
for r_name, row in d['covariance_analysis']['correlation_matrix'].items():
    print(f"  {r_name:<18s}: { {k: round(v, 2) for k, v in row.items()} }")
print("="*80)
