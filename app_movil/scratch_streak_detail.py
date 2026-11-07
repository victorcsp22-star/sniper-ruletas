import csv

with open(r"C:\Users\victo\nuevas_ruletas\ledger_nuevas_ruletas.csv", "r", encoding="utf-8", errors="ignore") as f:
    rows = list(csv.DictReader(f))

last_win_idx = -1
for i in range(len(rows)-1, -1, -1):
    cob = float(rows[i].get("cobrado", 0.0) or 0.0)
    pnl = float(rows[i].get("pnl", 0.0) or 0.0)
    if cob > 0 or pnl > 0:
        last_win_idx = i
        break

w = rows[last_win_idx]
print(f"ULTIMA VICTORIA: {w.get('fecha')} {w.get('hora')} en {w.get('ruleta')} | Cobrado: ${w.get('cobrado')} | PnL: ${w.get('pnl')}")

print("\n--- DETALLE DE LOS FALLOS EN ESTA RACHA ---")
tot_cost = 0.0
for idx, r in enumerate(rows[last_win_idx+1:], 1):
    bet = float(r.get("total_bet", 0.0) or 0.0)
    tot_cost += bet
    cands_clean = r.get("candidatos", "").split("[")[0].strip() if "[" in r.get("candidatos", "") else r.get("candidatos", "")
    print(f"#{idx:02d} | {r.get('fecha')} {r.get('hora'):<8} | {r.get('ruleta'):<26} | Jugados: {r.get('candidatos')} | Salio: {r.get('resultado')} | Costo: -${bet:.2f}")

print(f"\nTotal invertido en los {len(rows)-1-last_win_idx} fallos consecutivos: ${tot_cost:.2f} USD")
