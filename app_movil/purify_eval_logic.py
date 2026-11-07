server_path = r'C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py'

with open(server_path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. En evaluate_and_update_all_pure:
# Cambiar: if ((stk in target_streaks and not is_anti and not is_quar) or is_markov):
text = text.replace(
    'if ((stk in target_streaks and not is_anti and not is_quar) or is_markov):',
    'if (stk in target_streaks and not is_anti and not is_quar):'
)

# 2. En handle_api_status:
# Cambiar: if is_markov: badge = ... elif stk in target_streaks ...
text = text.replace(
'''                if is_markov:
                    badge = "⚡ Markov Sniper"
                    conteo = "🚨 ¡DISPARAR MARKOV! (1)"
                    urg = 1
                elif stk in target_streaks and not is_anti:''',
'''                if stk in target_streaks and not is_anti:'''
)

# Cambiar condición en handle_api_status:
text = text.replace(
    'if ((stk in target_streaks and not is_anti and not is_quar) or is_markov) and r_name not in state.get("pending_bets", {}):',
    'if (stk in target_streaks and not is_anti and not is_quar) and r_name not in state.get("pending_bets", {}):'
)

# Remover 'is_markov': False de radar_items
text = text.replace('                    "is_markov": is_markov,\n', '                    "is_markov": False,\n')

with open(server_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("[*] Logica de disparo purificada 100% a la estrategia de Canasta Rezagados.")
