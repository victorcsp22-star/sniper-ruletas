import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(r"C:\Users\victo\nuevas_ruletas\app_movil")
import server_zero_dep

class DummyHandler:
    def __init__(self):
        self.headers = {}
    def send_json_response(self, data, code=200):
        self.data = data

h = DummyHandler()
server_zero_dep.SniperHandler.handle_api_status(h)
print("Active signals count:", len(h.data["active_signals"]))
for sig in h.data["active_signals"]:
    print(f"  • {sig['ruleta']}: {sig['tipo']} | {sig['candidatos_str']} | Costo: ${sig.get('costo')} | Salido: {sig.get('ultimo_salido')}")
