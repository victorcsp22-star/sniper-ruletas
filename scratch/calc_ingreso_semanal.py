import json

with open(r"C:\Users\victo\nuevas_ruletas\scratch\resumen_backtest_9ruletas.json") as f:
    d = json.load(f)

# Total semanas del análisis: 110 semanas (2 años)
total_sem = 110

pnl_plana = d["plana"]["pnl"]
pnl_pesos = d["pesos"]["pnl"]

avg_sem_plana = pnl_plana / total_sem
avg_sem_pesos = pnl_pesos / total_sem

# Calcular promedio sobre semanas exclusivamente ganadoras y sobre el total
with open(r"C:\Users\victo\nuevas_ruletas\scratch\resumen_dias_semanas_perdidas.json") as f:
    dw = json.load(f)

sem_gan_plana = dw["plana"]["sem_gan"]
sem_gan_pesos = dw["pesos"]["sem_gan"]

print(f"Total semanas evaluadas: {total_sem}")
print(f"PnL Total Plana: ${pnl_plana:,.2f} USD")
print(f"Promedio semanal Plana ($1.00 fijo): ${avg_sem_plana:,.2f} USD / semana")
print(f"Promedio mensual Plana (~4.33 sem):  ${avg_sem_plana * 4.33:,.2f} USD / mes")
print()
print(f"PnL Total Pesos: ${pnl_pesos:,.2f} USD")
print(f"Promedio semanal Pesos (1-10):       ${avg_sem_pesos:,.2f} USD / semana")
print(f"Promedio mensual Pesos (~4.33 sem):  ${avg_sem_pesos * 4.33:,.2f} USD / mes")
