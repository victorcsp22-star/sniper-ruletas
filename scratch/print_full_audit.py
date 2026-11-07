import json

with open("audit_results.json", "r", encoding="utf-8") as f:
    d = json.load(f)

print("="*75)
print("AUDITORÍA DE MÁXIMO TEÓRICO: 2 AÑOS COMPLETOS (110 SEMANAS)")
print("="*75)
for name, v in d["full_2y_comparison"].items():
    print(f"\n--- Estrategia: {name.upper()} ---")
    for k, val in v.items():
        if isinstance(val, float):
            print(f"  {k:<28s}: {val:,.2f}")
        else:
            print(f"  {k:<28s}: {val}")

print("\n" + "="*75)
print("MONTE CARLO (1,000 ITERACIONES DE REMUESTREO ESTOCÁSTICO)")
print("="*75)
for name, v in d["monte_carlo"].items():
    print(f"\n--- Monte Carlo: {name.upper()} ---")
    for k, val in v.items():
        if isinstance(val, float):
            print(f"  {k:<32s}: {val:,.2f}")
        else:
            print(f"  {k:<32s}: {val}")
