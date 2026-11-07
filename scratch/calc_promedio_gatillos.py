import csv, collections, datetime, json
import pandas as pd

# 1. Medir en el ledger real reciente (últimos 30 días con fechas reales)
ledger_path = r"C:\Users\victo\nuevas_ruletas\ledger_nuevas_ruletas.csv"
rows = []
with open(ledger_path, newline='', encoding='utf-8') as f:
    r = csv.DictReader(f)
    for row in r:
        rows.append(row)

fechas_ledger = collections.defaultdict(int)
for row in rows:
    fechas_ledger[row['fecha']] += 1

dias_ledger = len(fechas_ledger)
total_ops_ledger = len(rows)
avg_diario_ledger = total_ops_ledger / dias_ledger if dias_ledger > 0 else 0

# 2. Medir en el backtest de 2 años del sistema anterior (7 ruletas con La Granjita)
# Archivo de backtest previo conocido: 6,074 operaciones en 110 semanas (770 días aprox)
# Vamos a calcular con exactitud cargando los eventos del script de 9 ruletas y del de 7 ruletas

# Del backtest de 9 ruletas:
with open(r"C:\Users\victo\nuevas_ruletas\scratch\resumen_backtest_9ruletas.json") as f:
    d9 = json.load(f)

print(f"=== DATOS EMPÍRICOS DEL LEDGER EN VIVO ===")
print(f"Total días operados registrados: {dias_ledger}")
print(f"Total disparos reales: {total_ops_ledger}")
print(f"Promedio diario real en vivo (7 ruletas anteriores): {avg_diario_ledger:.2f} disparos/día")
print()

# Muestra de los últimos 10 días en el ledger
print("Últimos 7 días en el ledger:")
for fecha, cnt in sorted(fechas_ledger.items())[-7:]:
    print(f"  {fecha}: {cnt} disparos")
