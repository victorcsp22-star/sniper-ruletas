import sys, os
sys.path.append(r'C:/Users/victo/nuevas_ruletas')
from app_movil.server_zero_dep import RULETAS

with open(r'C:/Users/victo/nuevas_ruletas/config.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
current_r = None
for line in lines:
    for r in RULETAS:
        if f'"{r}":' in line:
            current_r = r
            break
    if current_r and '"lags":' in line:
        lags = RULETAS[current_r]['lags']
        line = f'        "lags": {lags},\n'
        current_r = None
    new_lines.append(line)

with open(r'C:/Users/victo/nuevas_ruletas/config.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('config.py actualizado al 100% línea por línea con los 8 lags maestros.')
