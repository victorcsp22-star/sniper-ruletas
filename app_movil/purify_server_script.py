import re

server_path = r'C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py'

with open(server_path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. ThreadingHTTPServer para evitar caidas o cuelgues HTTP
text = text.replace('from http.server import HTTPServer, SimpleHTTPRequestHandler', 'from http.server import HTTPServer, ThreadingHTTPServer, SimpleHTTPRequestHandler')
text = text.replace('server = HTTPServer(("0.0.0.0", port), SniperHandler)', 'server = ThreadingHTTPServer(("0.0.0.0", port), SniperHandler)')

# 2. Remover residuos de Markov de RULETAS
text = re.sub(r'"markov":\s*\{\},\s*', '', text)
text = re.sub(r'"mirror":\s*\{\},\s*', '', text)

# 3. Remover logica de Markov en get_current_streaks
markov_block = '''    # Comprobar Markov
    last_num = nums[-1] if nums else ""
    markov_target = cfg["markov"].get(last_num)
    is_markov = bool(markov_target and markov_target not in rec_set_now and markov_target not in blacklist)

    # Comprobar AntiCluster hoy
    last_date = dates[-1] if dates else ""
    day_nums = [nums[j] for j in range(len(nums)) if dates[j] == last_date]
    is_anti_blocked = bool(use_anti and len(day_nums) >= 2 and day_nums[-1] in day_nums[:-1])

    if is_markov:
        cands = [markov_target]
    else:
        cands = cands_lag_now if not is_anti_blocked else []'''

pure_block = '''    # Comprobar AntiCluster hoy
    last_date = dates[-1] if dates else ""
    day_nums = [nums[j] for j in range(len(nums)) if dates[j] == last_date]
    is_anti_blocked = bool(use_anti and len(day_nums) >= 2 and day_nums[-1] in day_nums[:-1])

    cands = cands_lag_now if not is_anti_blocked else []'''

if markov_block in text:
    text = text.replace(markov_block, pure_block)
    print('[+] Logica de candidatos en get_current_streaks purificada.')
else:
    print('[-] No se encontro coincidencia exacta de markov_block en get_current_streaks.')

# 4. Remover 'is_markov' del dict retornado por get_current_streaks
text = text.replace('        "is_markov": is_markov,\n', '        "is_markov": False,\n')

# 5. En evaluate_and_update_all_pure:
text = text.replace('is_markov = info.get("is_markov", False)\n        is_anti = info.get("is_anti_blocked", False)', 'is_markov = False\n        is_anti = info.get("is_anti_blocked", False)')
text = text.replace('f" Markov Sniper [{p_lbl}]" if is_markov else f" Canasta Rezagados [{p_lbl}]"', 'f"Canasta Rezagados 8 Lags [{p_lbl}]"')

# 6. En handle_api_status:
text = text.replace('is_markov = info.get("is_markov", False)\n                is_anti = info.get("is_anti_blocked", False)', 'is_markov = False\n                is_anti = info.get("is_anti_blocked", False)')
text = text.replace('f" Markov Sniper [{p_label}]" if is_markov else f" Canasta Rezagados [{p_label}]"', 'f"Canasta Rezagados 8 Lags [{p_label}]"')

with open(server_path, 'w', encoding='utf-8') as f:
    f.write(text)

print('[*] server_zero_dep.py saneado con ThreadingHTTPServer y sin residuos de Markov.')
