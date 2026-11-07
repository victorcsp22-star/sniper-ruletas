import os
import csv
import json

base_dir = r"C:\Users\victo\nuevas_ruletas"
app_dir = os.path.join(base_dir, "app_movil")
static_dir = os.path.join(app_dir, "static")

# Formato estandar del sistema
LEDGER_COLS = [
    "fecha", "hora", "ruleta", "candidatos", "cands_count", "zona_patron",
    "smart_mult", "stake_unit", "total_bet", "resultado", "condicion",
    "cobrado", "pnl", "saldo", "peak", "drawdown_pct"
]

# Construir tabla limpia y homogenea
clean_rows = [
    {"fecha": "2026-11-01", "hora": "9:00 AM", "ruleta": "Guacharo Activo", "candidatos": "#21 GALLO, #24 IGUANA, #46 PUMA", "cands_count": 3, "zona_patron": "Rezagados [P:7/10]", "smart_mult": 1.0, "stake_unit": 100.0, "total_bet": 300.0, "resultado": "[37] TORTUGA", "condicion": "PERDIDA", "cobrado": 0.0, "pnl": -300.0, "saldo": 19700.0, "peak": 20000.0, "drawdown_pct": 1.5},
    {"fecha": "2026-11-01", "hora": "11:00 AM", "ruleta": "Guacharo Activo", "candidatos": "#27 PERRO, #39 LECHUZA", "cands_count": 2, "zona_patron": "Rezagados [P:7/10]", "smart_mult": 1.0, "stake_unit": 100.0, "total_bet": 200.0, "resultado": "[33] PESCADO", "condicion": "PERDIDA", "cobrado": 0.0, "pnl": -200.0, "saldo": 19500.0, "peak": 20000.0, "drawdown_pct": 2.5},
    {"fecha": "2026-11-01", "hora": "12:10 PM", "ruleta": "Lotto Gato", "candidatos": "#15 ZORRO", "cands_count": 1, "zona_patron": "Rezagados [P:6/10]", "smart_mult": 1.0, "stake_unit": 100.0, "total_bet": 100.0, "resultado": "[25] GALLINA", "condicion": "PERDIDA", "cobrado": 0.0, "pnl": -100.0, "saldo": 19400.0, "peak": 20000.0, "drawdown_pct": 3.0},
    {"fecha": "2026-11-01", "hora": "1:30 PM", "ruleta": "Granja Millonaria - Granjazo", "candidatos": "#02 TORO, #06 RANA, #60 TIBURON", "cands_count": 3, "zona_patron": "Rezagados [P:8/10]", "smart_mult": 1.0, "stake_unit": 100.0, "total_bet": 300.0, "resultado": "[34] VENADO", "condicion": "PERDIDA", "cobrado": 0.0, "pnl": -300.0, "saldo": 19100.0, "peak": 20000.0, "drawdown_pct": 4.5},
    {"fecha": "2026-11-01", "hora": "1:40 PM", "ruleta": "Gatazo", "candidatos": "#41 CANGURO, #55 OSO, #73 HIPO", "cands_count": 3, "zona_patron": "Rezagados [P:10/10]", "smart_mult": 1.0, "stake_unit": 100.0, "total_bet": 300.0, "resultado": "[48] PUERCOESPIN", "condicion": "PERDIDA", "cobrado": 0.0, "pnl": -300.0, "saldo": 18800.0, "peak": 20000.0, "drawdown_pct": 6.0},
    {"fecha": "2026-11-01", "hora": "2:00 PM", "ruleta": "Mega Animal 40", "candidatos": "#0 DELFIN", "cands_count": 1, "zona_patron": "Rezagados [P:4/10]", "smart_mult": 1.0, "stake_unit": 100.0, "total_bet": 100.0, "resultado": "[36] CULEBRA", "condicion": "PERDIDA", "cobrado": 0.0, "pnl": -100.0, "saldo": 18700.0, "peak": 20000.0, "drawdown_pct": 6.5},
    {"fecha": "2026-11-01", "hora": "3:00 PM", "ruleta": "Guacharo Activo", "candidatos": "#13 MONO, #18 BURRO", "cands_count": 2, "zona_patron": "Rezagados [P:7/10]", "smart_mult": 1.0, "stake_unit": 100.0, "total_bet": 200.0, "resultado": "[30] CAIMAN", "condicion": "PERDIDA", "cobrado": 0.0, "pnl": -200.0, "saldo": 18500.0, "peak": 20000.0, "drawdown_pct": 7.5},
    {"fecha": "2026-11-01", "hora": "3:40 PM", "ruleta": "Gatazo", "candidatos": "#21 GALLO", "cands_count": 1, "zona_patron": "Rezagados [P:8/10]", "smart_mult": 1.0, "stake_unit": 100.0, "total_bet": 100.0, "resultado": "[7] PERICO", "condicion": "PERDIDA", "cobrado": 0.0, "pnl": -100.0, "saldo": 18400.0, "peak": 20000.0, "drawdown_pct": 8.0},
    {"fecha": "2026-11-01", "hora": "5:00 PM", "ruleta": "Guacharo Activo", "candidatos": "#1 CARNERO, #17 PAVO, #40 AVISPA", "cands_count": 3, "zona_patron": "Rezagados [P:7/10]", "smart_mult": 1.0, "stake_unit": 100.0, "total_bet": 300.0, "resultado": "[10] TIGRE", "condicion": "PERDIDA", "cobrado": 0.0, "pnl": -300.0, "saldo": 18100.0, "peak": 20000.0, "drawdown_pct": 9.5},
    {"fecha": "2026-11-02", "hora": "10:00 AM", "ruleta": "Guacharo Activo", "candidatos": "#2 TORO [P:4/10]", "cands_count": 1, "zona_patron": "Markov Sniper [P:4/10]", "smart_mult": 1.0, "stake_unit": 100.0, "total_bet": 100.0, "resultado": "[63] CANGREJO", "condicion": "PERDIDA", "cobrado": 0.0, "pnl": -100.0, "saldo": 18000.0, "peak": 20000.0, "drawdown_pct": 10.0},
    {"fecha": "2026-11-02", "hora": "10:00 AM", "ruleta": "Mega Animal 40", "candidatos": "#0 DELFIN [P:3/10]", "cands_count": 1, "zona_patron": "Markov Sniper [P:3/10]", "smart_mult": 1.0, "stake_unit": 100.0, "total_bet": 100.0, "resultado": "[12] CABALLO", "condicion": "PERDIDA", "cobrado": 0.0, "pnl": -100.0, "saldo": 17900.0, "peak": 20000.0, "drawdown_pct": 10.5}
]

for p in [os.path.join(base_dir, "ledger_nuevas_ruletas.csv"), os.path.join(app_dir, "ledger_nuevas_ruletas.csv"), os.path.join(static_dir, "ledger_nuevas_ruletas.csv")]:
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LEDGER_COLS)
        w.writeheader()
        w.writerows(clean_rows)

print("Ledger escrito perfectamente en todas las ubicaciones!")
