import os
import sys
import json
import shutil
import pandas as pd
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = r"C:\Users\victo\nuevas_ruletas"
STATE_FILE = os.path.join(ROOT_DIR, "state_nuevas_ruletas.json")
LEDGER_FILE = os.path.join(ROOT_DIR, "ledger_nuevas_ruletas.csv")
REPLAY_SUMMARY_FILE = os.path.join(ROOT_DIR, "scratch", "specialized_live_replay.json")

# 1. Backups
shutil.copy2(STATE_FILE, STATE_FILE + ".before_specialized_backup")
shutil.copy2(LEDGER_FILE, LEDGER_FILE + ".before_specialized_backup")
print("✅ Respaldos creados: state_nuevas_ruletas.json.before_specialized_backup y ledger_nuevas_ruletas.csv.before_specialized_backup")

# 2. Cargar datos del replay auditado
with open(REPLAY_SUMMARY_FILE, "r", encoding="utf-8") as f:
    replay_data = json.load(f)

trades = replay_data["trades"]

# 3. Escribir nuevo ledger_nuevas_ruletas.csv
cols = [
    "fecha", "hora", "ruleta", "candidatos", "cands_count", "zona_patron",
    "smart_mult", "stake_unit", "total_bet", "resultado", "condicion",
    "cobrado", "pnl", "saldo", "peak", "drawdown_pct"
]
df_ledger = pd.DataFrame(trades)[cols]
df_ledger.to_csv(LEDGER_FILE, index=False, encoding="utf-8")
print(f"✅ Nuevo ledger guardado con {len(df_ledger)} operaciones auditadas.")

# 4. Leer estado actual para preservar configuraciones y actualizar con los números del nuevo sistema
with open(STATE_FILE, "r", encoding="utf-8") as f:
    st = json.load(f)

cycle_start_b = 247.25

st["bankroll"] = replay_data["bankroll"]
st["initial_bankroll"] = 200.0
st["peak_bankroll"] = replay_data["peak"]
st["created_at"] = "2026-10-17T09:47:00"
st["last_updated"] = datetime.now().isoformat()
st["cycle_number"] = 2
st["cycle_start_time"] = "2026-10-24T10:00:00"
st["cycle_start_bankroll"] = cycle_start_b
st["cycle_pnl"] = round(replay_data["bankroll"] - cycle_start_b, 2)
st["total_invested"] = replay_data["total_invested"]
st["total_collected"] = replay_data["total_collected"]
st["total_pnl"] = round(replay_data["bankroll"] - 200.0, 2)
st["wins"] = replay_data["wins"]
st["losses"] = replay_data["losses"]

# Limpiar apuestas pendientes para que el bot las regenere en caliente con el estado actual
st["pending_bets"] = {}

with open(STATE_FILE, "w", encoding="utf-8") as f:
    json.dump(st, f, indent=2, ensure_ascii=False)

print(f"✅ Nuevo estado guardado exitosamente: Bankroll ${st['bankroll']} USD | Peak ${st['peak_bankroll']} USD | PnL +${st['total_pnl']} USD")
