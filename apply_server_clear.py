import os

server_path = "C:/Users/victo/nuevas_ruletas/app_movil/server_zero_dep.py"
with open(server_path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update do_POST router
old_post = """    def do_POST(self):
        if self.path == "/api/sync":
            self.handle_api_sync()
        elif self.path == "/api/ingresar_sorteo":
            self.handle_api_ingresar_sorteo()
        else:
            self.send_error(404, "Endpoint no encontrado")"""

new_post = """    def do_POST(self):
        if self.path == "/api/sync":
            self.handle_api_sync()
        elif self.path == "/api/ingresar_sorteo":
            self.handle_api_ingresar_sorteo()
        elif self.path == "/api/clear_today_ledger":
            self.handle_api_clear_today_ledger()
        else:
            self.send_error(404, "Endpoint no encontrado")"""

# 2. Add handle_api_clear_today_ledger method
handler_method = """    def handle_api_clear_today_ledger(self):
        \"\"\"Elimina y archiva el registro de jugadas del día para no saturar la pantalla ni la memoria.\"\"\"
        try:
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            lpath = get_ledger_write_path()
            removed_count = 0
            if os.path.exists(lpath):
                archive_path = os.path.join(ROOT_DIR, "ledger_archive.csv")
                with open(lpath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                
                if lines:
                    header = lines[0]
                    kept_lines = [header]
                    archived_lines = []
                    for line in lines[1:]:
                        if line.startswith(today_str):
                            archived_lines.append(line)
                            removed_count += 1
                        else:
                            kept_lines.append(line)
                    
                    if archived_lines:
                        file_exists = os.path.exists(archive_path) and os.path.getsize(archive_path) > 0
                        with open(archive_path, "a", encoding="utf-8") as af:
                            if not file_exists:
                                af.write(header)
                            af.writelines(archived_lines)
                    
                    with open(lpath, "w", encoding="utf-8") as f:
                        f.writelines(kept_lines)
            
            state = load_state_pure()
            state["last_ledger_purge"] = datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
            save_state_pure(state)
            
            self.send_json_response({
                "status": "ok", 
                "message": f"Registro diario vaciado con éxito ({removed_count} operaciones archivadas en el historial).",
                "removed_count": removed_count
            })
        except Exception as e:
            self.send_json_response({"status": "error", "message": str(e)}, 500)
"""

c_norm = code.replace("\r\n", "\n")
o_norm = old_post.replace("\r\n", "\n")
n_norm = new_post.replace("\r\n", "\n")

if o_norm in c_norm:
    c_norm = c_norm.replace(o_norm, n_norm + "\n\n" + handler_method, 1)
    with open(server_path, "w", encoding="utf-8") as f:
        f.write(c_norm)
    print("Updated server_zero_dep.py with clear_today_ledger successfully.")
else:
    print("Could not find old_post router in server_zero_dep.py.")
