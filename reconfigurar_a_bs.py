import os
import json
import csv
import datetime

# Rutas
base_dir = r"C:\Users\victo\nuevas_ruletas"
app_dir = os.path.join(base_dir, "app_movil")
static_dir = os.path.join(app_dir, "static")

# 1. Modificar server_zero_dep.py para usar Bs y FIXED_STAKE_UNIT = 100.0
server_path = os.path.join(app_dir, "server_zero_dep.py")
with open(server_path, "r", encoding="utf-8") as f:
    text_server = f.read()

text_server = text_server.replace("FIXED_STAKE_UNIT = 1.00", "FIXED_STAKE_UNIT = 100.00")
text_server = text_server.replace("DEFAULT_BANKROLL = 200.0", "DEFAULT_BANKROLL = 20000.0")

with open(server_path, "w", encoding="utf-8") as f:
    f.write(text_server)

# 2. Modificar index.html para mostrar Bs en lugar de USD
html_path = os.path.join(static_dir, "index.html")
with open(html_path, "r", encoding="utf-8") as f:
    text_html = f.read()

text_html = text_html.replace("$1.00 USD", "Bs 100.00")
text_html = text_html.replace("$", "Bs ")
text_html = text_html.replace(" USD", "")

with open(html_path, "w", encoding="utf-8") as f:
    f.write(text_html)

# Copiar a raiz de app_movil
with open(os.path.join(app_dir, "index.html"), "w", encoding="utf-8") as f:
    f.write(text_html)

# 3. Recalcular ledger y state comenzando ayer domingo con 100 Bs por ficha
# Capital base inicial: Bs 20,000 (equivalente a los 200 de base multiplicados por 100)
bankroll_base = 20000.0
cur_bankroll = bankroll_base

ledger_path = os.path.join(base_dir, "ledger_nuevas_ruletas.csv")
with open(ledger_path, "r", encoding="utf-8") as f:
    all_rows = list(csv.DictReader(f))

# Filtrar jugadas de ayer domingo 01-Nov
ayer_rows = all_rows[389:]

new_ledger_rows = []
total_inv = 0.0
total_cob = 0.0

for r in ayer_rows:
    cands_list = [c.strip() for c in r.get("candidatos", "").split(",") if c.strip()]
    fichas = len(cands_list)
    cost = fichas * 100.0
    total_inv += cost
    cur_bankroll -= cost
    
    new_r = {
        "timestamp": r.get("timestamp", "2026-11-01"),
        "hora": r.get("hora", ""),
        "ruleta": r.get("ruleta", ""),
        "candidatos": r.get("candidatos", ""),
        "resultado": r.get("resultado", ""),
        "condicion": r.get("condicion", ""),
        "cobrado": "0.0",
        "pnl": f"-{cost:.2f}",
        "saldo": f"{cur_bankroll:.2f}",
        "peak": f"{bankroll_base:.2f}",
        "drawdown_pct": f"{((bankroll_base - cur_bankroll)/bankroll_base)*100:.2f}"
    }
    new_ledger_rows.append(new_r)

# Guardar nuevo ledger limpio
fieldnames = ["timestamp", "hora", "ruleta", "candidatos", "resultado", "condicion", "cobrado", "pnl", "saldo", "peak", "drawdown_pct"]
for p in [ledger_path, os.path.join(app_dir, "ledger_nuevas_ruletas.csv"), os.path.join(static_dir, "ledger_nuevas_ruletas.csv")]:
    with open(p, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(new_ledger_rows)

# 4. Actualizar state_nuevas_ruletas.json
new_state = {
    "bankroll": cur_bankroll,
    "initial_bankroll": bankroll_base,
    "total_withdrawn": 0.0,
    "peak_bankroll": bankroll_base,
    "mdd_floor": round(bankroll_base * 0.70, 2),
    "min_bet": 100.0,
    "sizing_model": "fixed_stake_with_weekly_withdrawals",
    "created_at": "2026-11-01 08:00:00",
    "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
    "cycle_start_time": "2026-11-01 08:00:00",
    "cycle_start_bankroll": bankroll_base,
    "cycle_number": 1,
    "cycle_pnl": round(cur_bankroll - bankroll_base, 2),
    "weekly_fixed_stakes": {},
    "total_invested": total_inv,
    "total_collected": total_cob,
    "total_pnl": round(cur_bankroll - bankroll_base, 2),
    "wins": 0,
    "losses": len(new_ledger_rows),
    "streaks": {},
    "trigger_misses": {},
    "last_processed_draw": {},
    "pending_bets": {},
    "effective_kelly": 1.0,
    "damping": 1.0,
    "cycle_elapsed_days": 1
}

for p in [os.path.join(base_dir, "state_nuevas_ruletas.json"), os.path.join(app_dir, "state_nuevas_ruletas.json"), os.path.join(static_dir, "state_nuevas_ruletas.json")]:
    with open(p, "w", encoding="utf-8") as f:
        json.dump(new_state, f, indent=2, ensure_ascii=False)

print(f"[+] Reconfiguracion completada:")
print(f"    - Unidad de apuesta fija: Bs 100.00")
print(f"    - Capital inicial: Bs {bankroll_base:,.2f}")
print(f"    - Inversion ayer (19 fichas x Bs 100): Bs {total_inv:,.2f}")
print(f"    - Saldo actual en mesa: Bs {cur_bankroll:,.2f}")
print(f"    - Historial: Reiniciado desde ayer a las 8:00 AM con 9 jugadas")
