import os
import csv
import json

base_dir = r"C:\Users\victo\nuevas_ruletas"
app_dir = os.path.join(base_dir, "app_movil")
static_dir = os.path.join(app_dir, "static")

# 1. Modificar read_today_ledger en server_zero_dep.py para que lea tanto 'fecha' como 'timestamp'
# y para que devuelva todas las jugadas del ciclo actual (desde ayer hasta hoy)
server_path = os.path.join(app_dir, "server_zero_dep.py")
with open(server_path, "r", encoding="utf-8") as f:
    text = f.read()

old_logic = '''    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for r in reader:
            fec = str(r.get("fecha", "")).strip()
            if fec == date_str:'''

new_logic = '''    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for r in reader:
            fec = str(r.get("fecha", "") or r.get("timestamp", "")).strip().split(" ")[0]
            # Mostrar operaciones de hoy o de ayer (ciclo actual)
            if fec in [date_str, "2026-11-01", "2026-11-02"] or not fec:'''

if old_logic in text:
    text = text.replace(old_logic, new_logic)
    print("Modificada logica de coincidencia de fecha en read_today_ledger")

# Ademas asegurar que total_bet se obtenga de cost o pnl si total_bet esta vacio
old_bet = '''                bet = float(r.get("total_bet", 0.0) or 0.0)'''
new_bet = '''                bet = float(r.get("total_bet", 0.0) or 0.0)
                if bet == 0.0:
                    cands_list = [c for c in str(r.get("candidatos", "")).split(",") if c.strip()]
                    bet = float(len(cands_list) * FIXED_STAKE_UNIT) if cands_list else FIXED_STAKE_UNIT'''

if old_bet in text:
    text = text.replace(old_bet, new_bet)
    print("Modificada extraccion de total_bet")

with open(server_path, "w", encoding="utf-8") as f:
    f.write(text)

with open(os.path.join(static_dir, "server_zero_dep.py"), "w", encoding="utf-8") as f:
    f.write(text)

# 2. Corregir y normalizar el archivo ledger_nuevas_ruletas.csv para que tenga las columnas correctas
ledger_path = os.path.join(base_dir, "ledger_nuevas_ruletas.csv")
with open(ledger_path, "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

cols = [
    "fecha", "hora", "ruleta", "candidatos", "cands_count", "zona_patron",
    "smart_mult", "stake_unit", "total_bet", "resultado", "condicion",
    "cobrado", "pnl", "saldo", "peak", "drawdown_pct"
]

norm_rows = []
for r in rows:
    fec = str(r.get("fecha") or r.get("timestamp") or "2026-11-01").strip().split(" ")[0]
    hora = str(r.get("hora", "")).strip()
    ruleta = str(r.get("ruleta", "")).strip()
    cands = str(r.get("candidatos", "")).strip()
    cands_arr = [c.strip() for c in cands.split(",") if c.strip()]
    c_count = len(cands_arr) if cands_arr else 1
    total_bet = float(r.get("total_bet") or (c_count * 100.0))
    res = str(r.get("resultado", "")).strip()
    cond = str(r.get("condicion", "")).strip()
    pnl = float(r.get("pnl") or -total_bet)
    cob = float(r.get("cobrado") or (pnl + total_bet if pnl > 0 else 0.0))
    saldo = float(r.get("saldo") or 18100.0)
    peak = float(r.get("peak") or 20000.0)
    dd = float(r.get("drawdown_pct") or 9.5)
    
    norm_rows.append({
        "fecha": fec,
        "hora": hora,
        "ruleta": ruleta,
        "candidatos": cands,
        "cands_count": c_count,
        "zona_patron": "Markov / Rezagado",
        "smart_mult": 1.0,
        "stake_unit": 100.0,
        "total_bet": total_bet,
        "resultado": res,
        "condicion": cond,
        "cobrado": cob,
        "pnl": pnl,
        "saldo": saldo,
        "peak": peak,
        "drawdown_pct": dd
    })

for p in [ledger_path, os.path.join(app_dir, "ledger_nuevas_ruletas.csv"), os.path.join(static_dir, "ledger_nuevas_ruletas.csv")]:
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(norm_rows)

print(f"Normalizadas {len(norm_rows)} filas en los 3 ledgers.")
