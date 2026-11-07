import json

p_state = r"C:\Users\victo\nuevas_ruletas\app_movil\state_nuevas_ruletas.json"
state = {
    "bankroll": 17900.0,
    "initial_bankroll": 20000.0,
    "cycle_start_bankroll": 20000.0,
    "total_withdrawn": 0.0,
    "cycle_number": 1,
    "peak_bankroll": 20000.0,
    "last_date": "2026-11-02",
    "pending_bets": {}
}

with open(p_state, 'w', encoding='utf-8') as f:
    json.dump(state, f, indent=4)

print("Estado de wallet restaurado con saldo auditado de Bs 17,900.00.")
