import os

bot_path = "C:/Users/victo/nuevas_ruletas/bot_nuevas_ruletas.py"
with open(bot_path, "r", encoding="utf-8") as f:
    code = f.read()

target1 = """                    if SIZING_MODEL == "fixed_stake_with_weekly_withdrawals":
                        final_stake = FIXED_STAKE_UNIT
                        r_card["stake_unit"] = final_stake
                        r_card["total_stake"] = round(cost_fichas * final_stake, 2)
                        r_card["posible_premio"] = round(final_stake * cfg["payout"], 2)"""

replacement1 = """                    if SIZING_MODEL == "fixed_stake_with_weekly_withdrawals":
                        final_stake = stake_unit
                        r_card["stake_unit"] = final_stake
                        r_card["total_stake"] = round(cost_fichas * final_stake, 2)
                        r_card["posible_premio"] = round(final_stake * cfg["payout"], 2)"""

target2 = """            for s in active_signals:
                print(f" 🚨 ¡ENTRADA INMINENTE ACTIVADA! -> {s['ruleta']} (Payout: {s['payout']:.0f}x)")
                print(f"    • ESTADO:                   {s['conteo_str']} | Racha Actual: {s['racha']}")
                print(f"    • Último Sorteo Salido:     {s['last_salido_str']}")"""

replacement2 = """            for s in active_signals:
                print(f" 🚨 ¡ENTRADA INMINENTE ACTIVADA! -> {s['ruleta']} [{s['color_badge']}] (Payout: {s['payout']:.0f}x)")
                print(f"    • ESTADO:                   {s['conteo_str']} | Racha Actual: {s['racha']}")
                print(f"    • BURBUJA 30 DÍAS:          {s['color_emoji']} {s['color_bubble']} (Stake: ${s['stake_unit']:.2f} USD)")
                print(f"    • Último Sorteo Salido:     {s['last_salido_str']}")"""

target3 = """        headers = f" {'RULETA':<19} | {'ESTADO ACTUAL':<19} | {'FALLOS QUE FALTAN':<22} | {'ÚLTIMO SALIDO (HORA)':<26} | {'ANIMALES A COMPRAR':<26} | {'MONTO C/U':<11} | {'TOTAL':<11} | {'PREMIO':<11} | {'CONDICIÓN PATRÓN'}"
        print(headers)
        print("-" * 165)

        for item in all_radar_items:
            if item["fallos_restantes"] == 0:
                # Entrada Inminente: Revelar números, nombres y montos exactos
                c_text = item['candidates_str']
                if len(c_text) > 24:
                    c_text = c_text[:22] + ".."
                c_display = f"{c_text} ({item['total_cands']})"
                apuesta_str = f"${item['stake_unit']:.2f}"
                total_str = f"💰 ${item['total_stake']:.2f}"
                premio_str = f"🏆 ${item['posible_premio']:.2f}"
            else:
                # En espera de fallo: Mantener oculto para no confundir
                c_display = "🔒 Oculto (Tras fallo)"
                apuesta_str = "---"
                total_str = "---"
                premio_str = "---"

            u_salido = item.get("last_salido_str", "---")
            if len(u_salido) > 25:
                u_salido = u_salido[:23] + ".."

            row = f" {item['ruleta']:<19} | {item['badge']:<19} | {item['conteo_str']:<22} | {u_salido:<26} | {c_display:<26} | {apuesta_str:<11} | {total_str:<11} | {premio_str:<11} | {item['smart_label']}"
            print(row)"""

replacement3 = """        headers = f" {'RULETA':<19} | {'BURBUJA 30D':<13} | {'ESTADO ACTUAL':<19} | {'FALLOS QUE FALTAN':<22} | {'ÚLTIMO SALIDO (HORA)':<26} | {'ANIMALES A COMPRAR':<26} | {'MONTO C/U':<11} | {'TOTAL':<11} | {'PREMIO':<11} | {'CONDICIÓN PATRÓN'}"
        print(headers)
        print("-" * 179)

        for item in all_radar_items:
            if item["fallos_restantes"] == 0:
                # Entrada Inminente: Revelar números, nombres y montos exactos
                c_text = item['candidates_str']
                if len(c_text) > 24:
                    c_text = c_text[:22] + ".."
                c_display = f"{c_text} ({item['total_cands']})"
                apuesta_str = f"${item['stake_unit']:.2f}"
                total_str = f"💰 ${item['total_stake']:.2f}"
                premio_str = f"🏆 ${item['posible_premio']:.2f}"
            else:
                # En espera de fallo: Mantener oculto para no confundir
                c_display = "🔒 Oculto (Tras fallo)"
                apuesta_str = "---"
                total_str = "---"
                premio_str = "---"

            u_salido = item.get("last_salido_str", "---")
            if len(u_salido) > 25:
                u_salido = u_salido[:23] + ".."

            b_badge = f"{item.get('color_emoji', '🟡')} ${item.get('stake_unit', 1.0):.2f}"
            row = f" {item['ruleta']:<19} | {b_badge:<13} | {item['badge']:<19} | {item['conteo_str']:<22} | {u_salido:<26} | {c_display:<26} | {apuesta_str:<11} | {total_str:<11} | {premio_str:<11} | {item['smart_label']}"
            print(row)"""

c_norm = code.replace('\r\n', '\n')
t1_norm = target1.replace('\r\n', '\n')
r1_norm = replacement1.replace('\r\n', '\n')
t2_norm = target2.replace('\r\n', '\n')
r2_norm = replacement2.replace('\r\n', '\n')
t3_norm = target3.replace('\r\n', '\n')
r3_norm = replacement3.replace('\r\n', '\n')

print("Target 1 found:", t1_norm in c_norm)
print("Target 2 found:", t2_norm in c_norm)
print("Target 3 found:", t3_norm in c_norm)

c_norm = c_norm.replace(t1_norm, r1_norm, 1)
c_norm = c_norm.replace(t2_norm, r2_norm, 1)
c_norm = c_norm.replace(t3_norm, r3_norm, 1)

with open(bot_path, "w", encoding="utf-8") as f:
    f.write(c_norm)

print("Saved bot_nuevas_ruletas.py successfully.")
