with open(r"C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py", "r", encoding="utf-8") as f:
    text = f.read()

bad_block = '''        def do_POST(self):
        if self.path == "/api/sync":
            self.handle_api_sync()
        elif self.path == "/api/ingresar_sorteo":
            self.handle_api_ingresar_sorteo()
        else:
            self.send_error(404, "Endpoint no encontrado")'''

good_block = '''    def do_POST(self):
        if self.path == "/api/sync":
            self.handle_api_sync()
        elif self.path == "/api/ingresar_sorteo":
            self.handle_api_ingresar_sorteo()
        else:
            self.send_error(404, "Endpoint no encontrado")'''

text = text.replace(bad_block, good_block)

with open(r"C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py", "w", encoding="utf-8") as f:
    f.write(text)

with open(r"C:\Users\victo\nuevas_ruletas\app_movil\static\server_zero_dep.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Indentacion corregida con éxito.")
