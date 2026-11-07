import csv

with open(r"C:\Users\victo\nuevas_ruletas\ledger_nuevas_ruletas.csv", "r", encoding="utf-8", errors="ignore") as f:
    rows = list(csv.DictReader(f))

print("=== REBOTE ESTADÍSTICO TRAS VALLES PROFUNDOS (>= 20 FALLOS) ===")
for i, r in enumerate(rows):
    cob = float(r.get("cobrado", 0.0) or 0.0)
    if cob > 0:
        pre_loss = 0
        for k in range(i-1, -1, -1):
            if float(rows[k].get("cobrado", 0.0) or 0.0) > 0:
                break
            pre_loss += 1
        if pre_loss >= 20:
            rul = r.get("ruleta")
            fec = r.get("fecha")
            sub = rows[i+1:i+11]
            wins_in_10 = sum(1 for x in sub if float(x.get("cobrado", 0.0) or 0.0) > 0)
            pnl_next_10 = sum(float(x.get("pnl", 0.0) or 0.0) for x in sub)
            print(f"Valle {pre_loss} fallos -> Rompe: {fec} en {rul:<16} (+${cob:.0f}) | Sig. 10 tiros: {wins_in_10} aciertos | PnL neto: {'+' if pnl_next_10>=0 else ''}${pnl_next_10:.2f} USD")
