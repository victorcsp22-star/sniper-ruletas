p = r"C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py"
with open(p, 'r', encoding='utf-8') as f:
    code = f.read()

peso_func = '''def calcular_peso_agente_pure(r_name, streak, trigger_miss):
    """Agente evaluador por ruleta: devuelve (peso_1_10, label_corto)."""
    cfg = RULETAS.get(r_name, {})
    payout = cfg.get("payout", 30)
    wr_optimos = cfg.get("wr_optimos", [1])

    # Dim 1 - Posicion en racha (0-4 pts)
    if streak in wr_optimos:
        s_racha = 4
    elif streak <= 1:
        s_racha = 3
    elif streak <= 5:
        s_racha = 2
    elif streak <= 20:
        s_racha = 1
    else:
        s_racha = 0

    # Dim 2 - Factor de payout (0-3 pts)
    s_payout = 3 if payout >= 60 else (2 if payout >= 40 else 1)

    # Dim 3 - Rebote post-misses
    if trigger_miss == 0:
        s_miss = 3
    elif trigger_miss <= 2:
        s_miss = 2
    elif trigger_miss <= 5:
        s_miss = 1
    else:
        s_miss = 0

    total = min(10, max(1, s_racha + s_payout + s_miss))
    return total, f"P:{total}/10"
'''

idx = code.find('def get_current_streaks(r_name):')
code = code[:idx] + peso_func + '\n\n' + code[idx:]

with open(p, 'w', encoding='utf-8') as f:
    f.write(code)

print("calcular_peso_agente_pure agregado correctamente.")
