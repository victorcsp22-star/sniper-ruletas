import csv

trades = []
with open("ledger_nuevas_ruletas.csv", mode="r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    for row in reader:
        trades.append(row)

initial_capital = 200.0
peak = initial_capital
max_dd_pct = 0.0
max_dd_usd = 0.0
max_dd_trade = None

drawdown_events = []

for i, t in enumerate(trades, 1):
    saldo = float(t["saldo"])
    ledger_peak = float(t["peak"])
    ledger_dd = float(t["drawdown_pct"])
    if saldo > peak:
        peak = saldo
    
    dd_usd = peak - saldo
    dd_pct = (dd_usd / peak) * 100.0
    item = {
        "trade_num": i,
        "fecha": t["fecha"],
        "hora": t["hora"],
        "ruleta": t["ruleta"],
        "peak": peak,
        "saldo": saldo,
        "dd_usd": dd_usd,
        "dd_pct": dd_pct,
        "ledger_dd": ledger_dd,
        "candidatos": t["candidatos"],
        "total_bet": t["total_bet"],
        "resultado": t["resultado"],
        "condicion": t["condicion"],
        "pnl": t["pnl"]
    }
    drawdown_events.append(item)
    if dd_pct > max_dd_pct:
        max_dd_pct = dd_pct
        max_dd_usd = dd_usd
        max_dd_trade = item

sorted_dd = sorted(drawdown_events, key=lambda x: x["dd_pct"], reverse=True)

print("="*85)
print(f" AUDITORÍA DE MÁXIMO DRAWDOWN HISTÓRICO (TOTAL OPERACIONES: {len(trades)})")
print("="*85)
print(f" MÁXIMO DRAWDOWN ALCANZADO: {max_dd_pct:.2f}% (-${max_dd_usd:.2f} USD)")
print(f" Registrado en la Operación #{max_dd_trade['trade_num']}:")
print(f"   • Fecha y Hora:    {max_dd_trade['fecha']} a las {max_dd_trade['hora']}")
print(f"   • Ruleta:          {max_dd_trade['ruleta']}")
print(f"   • ATH Previo:      ${max_dd_trade['peak']:.2f} USD")
print(f"   • Saldo en Banca:  ${max_dd_trade['saldo']:.2f} USD")
print(f"   • Retroceso Neto:  -${max_dd_usd:.2f} USD")
print(f"   • Jugada:          {max_dd_trade['candidatos']} (Monto: ${max_dd_trade['total_bet']} USD)")
print(f"   • Salido Oficial:  {max_dd_trade['resultado']}")
print("-" * 85)
print(" TOP 5 PERIODOS CON MAYOR DRAWDOWN EN TODA LA PRUEBA:")
for rank, d in enumerate(sorted_dd[:5], 1):
    print(f" {rank}. Operación #{d['trade_num']:02d} ({d['fecha']} {d['hora']:>8s}) | {d['ruleta']:<16s} | DD: {d['dd_pct']:.2f}% (-${d['dd_usd']:.2f} USD) | Peak: ${d['peak']:.2f} -> Saldo: ${d['saldo']:.2f}")
print("="*85)
