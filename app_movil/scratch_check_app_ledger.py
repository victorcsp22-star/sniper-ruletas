import urllib.request, json

try:
    with urllib.request.urlopen("http://127.0.0.1:5000/api/status", timeout=3) as r:
        data = json.loads(r.read().decode("utf-8"))
        rec = data.get("recent_ledger", [])
        print(f"TOTAL EN RECENT_LEDGER DE LA APP: {len(rec)}")
        for i, op in enumerate(rec, 1):
            fec = op.get("fecha")
            hor = op.get("hora")
            rul = op.get("ruleta")
            can = op.get("candidatos")
            res = op.get("resultado")
            bet = op.get("total_bet")
            pnl = op.get("pnl")
            sal = op.get("saldo")
            print(f"#{i:02d} | {fec} {hor:<8} | {rul:<26} | Jugados: {can} | Salido: {res} | Bet: ${bet} | PnL: ${pnl} | Saldo: ${sal}")
except Exception as e:
    print("ERROR:", e)
