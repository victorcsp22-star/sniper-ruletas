import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(r"C:\Users\victo\nuevas_ruletas\app_movil")
import server_zero_dep

print("TESTEANDO OUTPUT DE SERVER_ZERO_DEP:")
for r_name in server_zero_dep.RULETAS.keys():
    stk, miss, info = server_zero_dep.get_current_streaks(r_name)
    print(f"{r_name:28}: Racha={stk:2} | is_markov={info.get('is_markov')} | cands={info.get('cands')} | last={info.get('last_str')}")
