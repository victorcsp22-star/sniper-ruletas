import os

base = "C:/Users/victo/nuevas_ruletas"
server_path = os.path.join(base, "app_movil", "server_zero_dep.py")

with open(server_path, "r", encoding="utf-8") as f:
    code = f.read()

target1 = """            # 1. Incluir primero las apuestas pendientes que ya están en el estado
            state = load_state_pure()
            for r_name, pb in state.get("pending_bets", {}).items():
                cfg = RULETAS.get(r_name, {})
                active_signals.append({
                    "ruleta": r_name,
                    "emoji": cfg.get("emoji", "🎯"),
                    "tipo": pb.get("smart_label", "🚨 Compra Activa"),
                    "candidatos": pb.get("candidatos", []),
                    "candidatos_str": pb.get("candidatos_str", ""),
                    "total_fichas": pb.get("total_cands", 1),
                    "costo": float(pb.get("total_stake", 1.0)),
                    "premio_potencial": float(pb.get("posible_premio", 30.0)),
                    "payout": float(pb.get("payout", 30.0)),
                    "peso_agente": pb.get("peso_agente", 5),
                    "peso_label": pb.get("peso_label", "P:5/10"),
                    "ultimo_salido": pb.get("last_salido_str", "---")
                })"""

replacement1 = """            # 1. Incluir primero las apuestas pendientes que ya están en el estado
            state = load_state_pure()
            for r_name, pb in state.get("pending_bets", {}).items():
                cfg = RULETAS.get(r_name, {})
                burbuja = color_bubbles.get(r_name, {
                    "color": "AMARILLO", "emoji": "🟡", "stake": 1.00, "rank": 4, 
                    "badge": "🟡 $1.00", "pnl_30d": 0.0, "color_hex": "#f59e0b"
                })
                active_signals.append({
                    "ruleta": r_name,
                    "emoji": cfg.get("emoji", "🎯"),
                    "tipo": pb.get("smart_label", "🚨 Compra Activa"),
                    "candidatos": pb.get("candidatos", []),
                    "candidatos_str": pb.get("candidatos_str", ""),
                    "total_fichas": pb.get("total_cands", 1),
                    "stake_unit": float(pb.get("stake_unit", burbuja["stake"])),
                    "costo": float(pb.get("total_stake", 1.0)),
                    "premio_potencial": float(pb.get("posible_premio", 30.0)),
                    "payout": float(pb.get("payout", 30.0)),
                    "peso_agente": pb.get("peso_agente", 5),
                    "peso_label": pb.get("peso_label", "P:5/10"),
                    "ultimo_salido": pb.get("last_salido_str", "---"),
                    "burbuja": burbuja
                })"""

target2 = """                p_agente, p_label = calcular_peso_agente_pure(r_name, stk, miss)

                # Si no estaba ya en pending_bets, agregar si califica
                is_quar = bool(QUARANTINE_MISSES > 0 and miss >= QUARANTINE_MISSES)
                if (stk in target_streaks and not is_anti and not is_quar) and r_name not in state.get("pending_bets", {}):
                    active_signals.append({
                        "ruleta": r_name,
                        "emoji": cfg["emoji"],
                        "tipo": f"⚡ Markov Sniper [{p_label}]" if is_markov else f"🎯 Canasta Rezagados [{p_label}]",
                        "candidatos": cands,
                        "candidatos_str": ", ".join([f"#{c['numero']} {c['animal']} [{p_label}]" for c in cands]),
                        "total_fichas": len(cands),
                        "costo": round(len(cands) * FIXED_STAKE_UNIT, 2),
                        "premio_potencial": round(FIXED_STAKE_UNIT * cfg["payout"], 2),
                        "payout": cfg["payout"],
                        "peso_agente": p_agente,
                        "peso_label": p_label,
                        "ultimo_salido": info.get("last_str", "---")
                    })

                radar_items.append({
                    "ruleta": r_name,
                    "emoji": cfg["emoji"],
                    "payout": cfg["payout"],
                    "racha": stk,
                    "misses": miss,
                    "badge": badge,
                    "conteo_str": conteo,
                    "urgencia": urg,
                    "peso_agente": p_agente,
                    "peso_label": p_label,
                    "ultimo_salido": info.get("last_str", "---"),
                    "is_markov": False,
                    "is_anti_blocked": is_anti
                })"""

replacement2 = """                p_agente, p_label = calcular_peso_agente_pure(r_name, stk, miss)
                burbuja = color_bubbles.get(r_name, {
                    "color": "AMARILLO", "emoji": "🟡", "stake": 1.00, "rank": 4, 
                    "badge": "🟡 $1.00", "pnl_30d": 0.0, "color_hex": "#f59e0b"
                })

                # Si no estaba ya en pending_bets, agregar si califica
                is_quar = bool(QUARANTINE_MISSES > 0 and miss >= QUARANTINE_MISSES)
                if (stk in target_streaks and not is_anti and not is_quar) and r_name not in state.get("pending_bets", {}):
                    active_signals.append({
                        "ruleta": r_name,
                        "emoji": cfg["emoji"],
                        "tipo": f"⚡ Markov Sniper [{p_label}]" if is_markov else f"🎯 Canasta Rezagados [{p_label}]",
                        "candidatos": cands,
                        "candidatos_str": ", ".join([f"#{c['numero']} {c['animal']} [{p_label}]" for c in cands]),
                        "total_fichas": len(cands),
                        "stake_unit": burbuja["stake"],
                        "costo": round(len(cands) * burbuja["stake"], 2),
                        "premio_potencial": round(burbuja["stake"] * cfg["payout"], 2),
                        "payout": cfg["payout"],
                        "peso_agente": p_agente,
                        "peso_label": p_label,
                        "ultimo_salido": info.get("last_str", "---"),
                        "burbuja": burbuja
                    })

                radar_items.append({
                    "ruleta": r_name,
                    "emoji": cfg["emoji"],
                    "payout": cfg["payout"],
                    "racha": stk,
                    "misses": miss,
                    "badge": badge,
                    "conteo_str": conteo,
                    "urgencia": urg,
                    "peso_agente": p_agente,
                    "peso_label": p_label,
                    "ultimo_salido": info.get("last_str", "---"),
                    "is_markov": False,
                    "is_anti_blocked": is_anti,
                    "burbuja": burbuja
                })"""

# Normalize newlines
c_norm = code.replace('\r\n', '\n')
t1_norm = target1.replace('\r\n', '\n')
r1_norm = replacement1.replace('\r\n', '\n')
t2_norm = target2.replace('\r\n', '\n')
r2_norm = replacement2.replace('\r\n', '\n')

print("Target 1 found:", t1_norm in c_norm)
print("Target 2 found:", t2_norm in c_norm)

c_norm = c_norm.replace(t1_norm, r1_norm, 1)
c_norm = c_norm.replace(t2_norm, r2_norm, 1)

with open(server_path, "w", encoding="utf-8") as f:
    f.write(c_norm)

print("Saved successfully.")
