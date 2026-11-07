import os

server_path = "C:/Users/victo/nuevas_ruletas/app_movil/server_zero_dep.py"
with open(server_path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update get_current_streaks to detect Markov
target_get_streaks = """    cands = cands_lag_now if not is_anti_blocked else []

    cands_formatted = [{"numero": c, "animal": animals.get(c, "")} for c in cands]
    last_row = rows[-1]
    last_str = f"#{last_row['numero']} {last_row['animal']} ({last_row['hora']})"

    return streak, trigger_misses, {
        "cands": cands_formatted,
        "is_markov": False,
        "is_anti_blocked": is_anti_blocked,
        "last_str": last_str,
        "last_num": last_row["numero"],
        "last_animal": last_row["animal"],
        "last_hora": last_row["hora"]
    }"""

replacement_get_streaks = """    last_row = rows[-1]
    last_str = f"#{last_row['numero']} {last_row['animal']} ({last_row['hora']})"
    last_num_str = str(last_row["numero"]).strip()

    # Comprobar Markov Sniper
    is_markov = False
    markov_snipers = cfg.get("markov_snipers", {})
    if last_num_str in markov_snipers:
        target_num = markov_snipers[last_num_str]
        if target_num not in rec_set_now and target_num not in blacklist:
            is_markov = True
            cands = [target_num]
            cands_formatted = [{"numero": target_num, "animal": animals.get(target_num, "")}]
        else:
            cands = cands_lag_now if not is_anti_blocked else []
            cands_formatted = [{"numero": c, "animal": animals.get(c, "")} for c in cands]
    else:
        cands = cands_lag_now if not is_anti_blocked else []
        cands_formatted = [{"numero": c, "animal": animals.get(c, "")} for c in cands]

    return streak, trigger_misses, {
        "cands": cands_formatted,
        "is_markov": is_markov,
        "is_anti_blocked": is_anti_blocked,
        "last_str": last_str,
        "last_num": last_row["numero"],
        "last_animal": last_row["animal"],
        "last_hora": last_row["hora"]
    }"""

code = code.replace(target_get_streaks, replacement_get_streaks)

# 2. Update evaluate_and_update_all_pure
target_eval = """    for r_name, cfg in RULETAS.items():
        stk, miss, info = get_current_streaks(r_name)
        is_markov = False
        is_anti = info.get("is_anti_blocked", False)
        cands = info.get("cands", [])
        target_streaks = cfg.get("target_streaks", [1])

        is_quar = bool(QUARANTINE_MISSES > 0 and miss >= QUARANTINE_MISSES)
        if (stk in target_streaks and not is_anti and not is_quar):"""

replacement_eval = """    color_bubbles = get_30d_color_bubbles(30)
    for r_name, cfg in RULETAS.items():
        stk, miss, info = get_current_streaks(r_name)
        is_markov = info.get("is_markov", False)
        is_anti = info.get("is_anti_blocked", False)
        cands = info.get("cands", [])
        target_streaks = cfg.get("target_streaks", [1])
        burbuja = color_bubbles.get(r_name, {"stake": 1.00})

        is_quar = bool(QUARANTINE_MISSES > 0 and miss >= QUARANTINE_MISSES)
        if ((stk in target_streaks or is_markov) and not is_anti and not is_quar):"""

code = code.replace(target_eval, replacement_eval)

# 3. Update handle_api_status radar & active signals loop
target_status_loop = """            for r_name, cfg in RULETAS.items():
                stk, miss, info = get_current_streaks(r_name)
                is_markov = False
                is_anti = info.get("is_anti_blocked", False)
                cands = info.get("cands", [])
                target_streaks = cfg.get("target_streaks", [1])

                if stk in target_streaks and not is_anti:
                    badge = f"🔥 Racha {stk} (Objetivo)"
                    conteo = "🚨 ¡DISPARAR AHORA! (0)"
                    urg = 1
                elif is_anti:
                    badge = "🛡️ AntiCluster"
                    conteo = "🛡️ Bloqueado por Repetición"
                    urg = 3
                elif stk < min(target_streaks):
                    badge = "🟢 Racha 0" if stk == 0 else f"🟡 Racha {stk}"
                    conteo = f"⚠️ Falta {min(target_streaks) - stk} fallo"
                    urg = 2
                else:
                    badge = f"🟡 Racha {stk}"
                    conteo = f"💤 Espera reinicio ({stk})"
                    urg = 3

                p_agente, p_label = calcular_peso_agente_pure(r_name, stk, miss)
                burbuja = color_bubbles.get(r_name, {
                    "color": "AMARILLO", "emoji": "🟡", "stake": 1.00, "rank": 4, 
                    "badge": "🟡 $1.00", "pnl_30d": 0.0, "color_hex": "#f59e0b"
                })

                # Si no estaba ya en pending_bets, agregar si califica
                is_quar = bool(QUARANTINE_MISSES > 0 and miss >= QUARANTINE_MISSES)
                if (stk in target_streaks and not is_anti and not is_quar) and r_name not in state.get("pending_bets", {}):"""

replacement_status_loop = """            for r_name, cfg in RULETAS.items():
                stk, miss, info = get_current_streaks(r_name)
                is_markov = info.get("is_markov", False)
                is_anti = info.get("is_anti_blocked", False)
                cands = info.get("cands", [])
                target_streaks = cfg.get("target_streaks", [1])

                if is_markov:
                    badge = "⚡ Markov Sniper"
                    conteo = "🚨 ¡DISPARAR MARKOV! (1)"
                    urg = 1
                elif stk in target_streaks and not is_anti:
                    badge = f"🔥 Racha {stk} (Objetivo)"
                    conteo = "🚨 ¡DISPARAR AHORA! (0)"
                    urg = 1
                elif is_anti:
                    badge = "🛡️ AntiCluster"
                    conteo = "🛡️ Bloqueado por Repetición"
                    urg = 3
                elif stk < min(target_streaks):
                    badge = "🟢 Racha 0" if stk == 0 else f"🟡 Racha {stk}"
                    conteo = f"⚠️ Falta {min(target_streaks) - stk} fallo"
                    urg = 2
                else:
                    badge = f"🟡 Racha {stk}"
                    conteo = f"💤 Espera reinicio ({stk})"
                    urg = 3

                p_agente, p_label = calcular_peso_agente_pure(r_name, stk, miss)
                burbuja = color_bubbles.get(r_name, {
                    "color": "AMARILLO", "emoji": "🟡", "stake": 1.00, "rank": 4, 
                    "badge": "🟡 $1.00", "pnl_30d": 0.0, "color_hex": "#f59e0b"
                })

                # Si no estaba ya en pending_bets, agregar si califica
                is_quar = bool(QUARANTINE_MISSES > 0 and miss >= QUARANTINE_MISSES)
                if ((stk in target_streaks or is_markov) and not is_anti and not is_quar) and r_name not in state.get("pending_bets", {}):"""

code = code.replace(target_status_loop, replacement_status_loop)

with open(server_path, "w", encoding="utf-8") as f:
    f.write(code)

print("Updated server_zero_dep.py with Markov & Bubbles successfully.")
