import os, sys, json, csv, re, datetime

# 1. Leer el archivo server_zero_dep.py actual
server_path = r"C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py"
with open(server_path, "r", encoding="utf-8") as f:
    code = f.read()

# Anadir la constante QUARANTINE_MISSES = 20 si no está
if "QUARANTINE_MISSES = 20" not in code:
    code = code.replace("DEFAULT_BANKROLL = 200.0", "DEFAULT_BANKROLL = 200.0\nQUARANTINE_MISSES = 20")

# Modificar el parser de tuazar para que Granjazo no falle
code = code.replace('cfg["title"].lower() in title', 'cfg["title"].lower() in title or (r_name == "Granja Millonaria - Granjazo" and "granjazo" in title)')

# Implementar endpoint POST /api/ingresar_sorteo en SniperHandler
endpoint_code = '''    def do_POST(self):
        if self.path == "/api/sync":
            self.handle_api_sync()
        elif self.path == "/api/ingresar_sorteo":
            self.handle_api_ingresar_sorteo()
        else:
            self.send_error(404, "Endpoint no encontrado")

    def handle_api_ingresar_sorteo(self):
        """Permite ingresar un resultado manualmente en 0.001s cuando no hay internet."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            req_json = json.loads(post_data.decode('utf-8'))
            
            r_name = req_json.get("ruleta")
            numero = str(req_json.get("numero", "")).strip()
            animal = str(req_json.get("animal", "")).strip()
            hora = req_json.get("hora") or datetime.datetime.now().strftime("%I:%M %p").lstrip("0")
            fecha = req_json.get("fecha") or datetime.date.today().strftime("%Y-%m-%d")
            
            if not r_name or r_name not in RULETAS or not numero:
                self.send_json_response({"status": "error", "message": "Datos incompletos"}, 400)
                return
                
            # Procesar el nuevo sorteo localmente de inmediato
            live_data = {r_name: [{"fecha": fecha, "hora": hora, "numero": numero, "animal": animal}]}
            new_counts = evaluate_and_update_all_pure(live_data)
            
            self.send_json_response({"status": "ok", "message": f"Sorteo registrado: {r_name} {hora} -> #{numero} {animal}", "counts": new_counts})
        except Exception as e:
            self.send_json_response({"status": "error", "message": str(e)}, 500)
'''

# Reemplazar do_POST
code = re.sub(r'def do_POST\(self\):.*?self\.send_error\(404, "Endpoint no encontrado"\)', endpoint_code, code, flags=re.DOTALL)

# Aplicar regla de Cuarentena en evaluate_and_update_all_pure y handle_api_status
# En evaluate_and_update_all_pure:
# if (stk in target_streaks and not is_anti) or is_markov:
# cambiar a:
# is_quar = bool(QUARANTINE_MISSES > 0 and miss >= QUARANTINE_MISSES)
# if ((stk in target_streaks and not is_anti and not is_quar) or is_markov):

code = code.replace(
    'if (stk in target_streaks and not is_anti) or is_markov:',
    'is_quar = bool(QUARANTINE_MISSES > 0 and miss >= QUARANTINE_MISSES)\n        if ((stk in target_streaks and not is_anti and not is_quar) or is_markov):'
)

# En handle_api_status:
code = code.replace(
    'if ((stk in target_streaks and not is_anti) or is_markov) and r_name not in state.get("pending_bets", {}):',
    'is_quar = bool(QUARANTINE_MISSES > 0 and miss >= QUARANTINE_MISSES)\n                if ((stk in target_streaks and not is_anti and not is_quar) or is_markov) and r_name not in state.get("pending_bets", {}):'
)

with open(server_path, "w", encoding="utf-8") as f:
    f.write(code)

with open(r"C:\Users\victo\nuevas_ruletas\app_movil\static\server_zero_dep.py", "w", encoding="utf-8") as f:
    f.write(code)

print("server_zero_dep.py actualizado con endpoint offline y Cuarentena Preventiva.")
