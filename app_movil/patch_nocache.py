import os

p = r"C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py"
with open(p, "r", encoding="utf-8") as f:
    t = f.read()

old = """    def do_GET(self):
        if self.path == "/api/status":
            self.handle_api_status()
        elif self.path == "/api/reporte":
            self.handle_api_reporte()
        else:
            super().do_GET()"""

new = """    def do_GET(self):
        if self.path == "/api/status":
            self.handle_api_status()
        elif self.path == "/api/reporte":
            self.handle_api_reporte()
        elif self.path == "/" or self.path.startswith("/index.html") or "?" in self.path:
            html_path = os.path.join(STATIC_DIR, "index.html")
            if not os.path.exists(html_path):
                html_path = os.path.join(ROOT_DIR, "index.html")
            try:
                with open(html_path, "rb") as f:
                    c = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(c)))
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.send_header("Pragma", "no-cache")
                self.send_header("Expires", "0")
                self.end_headers()
                self.wfile.write(c)
            except Exception:
                super().do_GET()
        else:
            super().do_GET()"""

if old in t:
    t = t.replace(old, new, 1)
    with open(p, "w", encoding="utf-8") as f:
        f.write(t)
    print("Modificado con exito!")
else:
    print("No encontro bloque exacto")
