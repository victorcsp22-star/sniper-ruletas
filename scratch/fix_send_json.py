import os
import shutil

p = 'C:/Users/victo/nuevas_ruletas/app_movil/server_zero_dep.py'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()

target = """    def send_json_response(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)"""

replacement = """    def send_json_response(self, data, code=200):
        try:
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            print(f"[-] Error enviando JSON: {e}")"""

if target in c:
    c = c.replace(target, replacement)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(c)
    print("Updated server_zero_dep.py successfully!")
    shutil.copyfile(p, 'C:/Users/victo/nuevas_ruletas/app_movil/static/server_zero_dep.py')
    print("Copied to static/server_zero_dep.py")
else:
    print("Target not found!")
