path = 'C:/Users/victo/nuevas_ruletas/app_movil/server_zero_dep.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

old_1 = 'if ((stk in target_streaks or is_markov) and not is_anti and not is_quar):'
new_1 = 'is_mirror = info.get("is_mirror", False)\n        if ((stk in target_streaks or is_markov or is_mirror) and not is_anti and not is_quar):'

old_2 = 'if ((stk in target_streaks or is_markov) and not is_anti and not is_quar) and r_name not in state.get("pending_bets", {}):'
new_2 = 'is_mirror = info.get("is_mirror", False)\n                if ((stk in target_streaks or is_markov or is_mirror) and not is_anti and not is_quar) and r_name not in state.get("pending_bets", {}):'

print('Found old_1:', old_1 in text)
print('Found old_2:', old_2 in text)

if old_1 in text and old_2 in text:
    text = text.replace(old_1, new_1)
    text = text.replace(old_2, new_2)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print('Replaced successfully!')
