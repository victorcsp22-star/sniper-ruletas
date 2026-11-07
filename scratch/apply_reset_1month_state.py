import os
import sys
import json
import pandas as pd
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = r"C:\Users\victo\nuevas_ruletas"
sys.path.append(ROOT_DIR)

from config import RULETAS_CONFIG, STATE_FILE, LEDGER_FILE, DIARIO_FILE

replay_json_path = os.path.join(ROOT_DIR, "scratch", "replay_1month_fixed1dollar_withdrawn.json")
with open(replay_json_path, "r", encoding="utf-8") as f:
    replay_data = json.load(f)

# 1. Escribir ledger_nuevas_ruletas.csv
cols = [
    "fecha", "hora", "ruleta", "candidatos", "cands_count", "zona_patron",
    "smart_mult", "stake_unit", "total_bet", "resultado", "condicion",
    "cobrado", "pnl", "saldo", "peak", "drawdown_pct"
]

rows = []
for r in replay_data["ledger_rows"]:
    row = {c: r.get(c, "") for c in cols}
    rows.append(row)

df_ledger = pd.DataFrame(rows, columns=cols)
df_ledger.to_csv(LEDGER_FILE, index=False, encoding="utf-8")
print(f"✅ Ledger CSV guardado con {len(df_ledger)} registros en: {LEDGER_FILE}")

# 2. Escribir diario_nuevas_ruletas.md
lines_diario = [
    "# 📓 Diario de Operaciones en Vivo: Sistema Multi-Ruleta ($1.00 Fijo con Retiro Semanal)\n",
    f"> **Ubicación:** `{ROOT_DIR}`  ",
    "> **Fecha de Inicio:** 2026-09-30 (Hace 1 Mes)  ",
    "> **Modelo de Capital:** $1.00 USD fijo por animalito | Retiro semanal de ganancias netas a la cartera.  \n",
    "## 📜 Registro Granular de Disparos y Resultados\n",
    "| Timestamp | Ruleta | Sorteo | Animales Apostados | Salido Oficial | Resultado | Invertido ($) | Cobrado ($) | PnL Disparo | Saldo en Mesa |",
    "| :--- | :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |"
]

for ev in replay_data["ledger_rows"]:
    badge = "🟢 GANADA" if ev["hit"] else "🔴 PERDIDA"
    pnl_str = f"{'+' if ev['pnl']>=0 else ''}${ev['pnl']:.2f}"
    lines_diario.append(f"| {ev['timestamp']} | {ev['ruleta']} | {ev['hora']} | `{ev['candidatos']}` | **#{ev['salido_num']} {ev['salido_anim']}** | {badge} | ${ev['inv']:.2f} | ${ev['cob']:.2f} | **{pnl_str}** | **${ev['bankroll']:.2f}** |")

with open(DIARIO_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(lines_diario))
print(f"✅ Diario Markdown guardado con {len(lines_diario)} líneas en: {DIARIO_FILE}")

# 3. Obtener últimos sorteos procesados y rachas exactas
from bot_nuevas_ruletas import calculate_current_streak_and_misses, get_history_series

streaks = {}
misses = {}
last_processed = {}

for r_name in RULETAS_CONFIG:
    if RULETAS_CONFIG[r_name].get("active", False):
        stk, miss = calculate_current_streak_and_misses(r_name)
        streaks[r_name] = stk
        misses[r_name] = miss
        _, df_r = get_history_series(r_name)
        if not df_r.empty:
            last_processed[r_name] = f"{df_r.iloc[-1]['fecha']} {df_r.iloc[-1]['hora']}"

# 4. Escribir state_nuevas_ruletas.json
new_state = {
    "bankroll": 240.00,
    "initial_bankroll": 200.00,
    "total_withdrawn": 734.00,
    "peak_bankroll": 240.00,
    "mdd_floor": 0.40,
    "min_bet": 0.10,
    "sizing_model": "fixed_stake_with_weekly_withdrawals",
    "created_at": "2026-09-30T00:00:00",
    "last_updated": datetime.now().isoformat(),
    "cycle_start_time": "2026-10-28T00:00:00",
    "cycle_start_bankroll": 200.00,
    "cycle_number": 5,
    "cycle_pnl": 40.00,
    "weekly_fixed_stakes": {r: 1.00 for r in RULETAS_CONFIG if RULETAS_CONFIG[r].get("active", False)},
    "total_invested": replay_data["total_invested"],
    "total_collected": replay_data["total_collected"],
    "total_pnl": replay_data["net_pnl_total"],
    "wins": replay_data["total_wins"],
    "losses": replay_data["total_ops"] - replay_data["total_wins"],
    "streaks": streaks,
    "trigger_misses": misses,
    "last_processed_draw": last_processed,
    "pending_bets": {}
}

with open(STATE_FILE, "w", encoding="utf-8") as f:
    json.dump(new_state, f, indent=2, ensure_ascii=False)

print(f"✅ State JSON guardado exitosamente en: {STATE_FILE}")
