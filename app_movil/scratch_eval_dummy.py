import sys
sys.path.append(r"C:\Users\victo\nuevas_ruletas\app_movil")
import server_zero_dep

class Dummy:
    def send_json_response(self, data, code=200):
        rec = data.get("recent_ledger", [])
        print(f"TOTAL RECENT_LEDGER: {len(rec)}")
        for i, op in enumerate(rec, 1):
            h = op.get("hora")
            r = op.get("ruleta")
            c = op.get("candidatos")
            res = op.get("resultado")
            bet = op.get("total_bet")
            print(f"#{i:02d} | {h:<8} | {r:<25} | {c} | Salido: {res} | ${bet}")

d = Dummy()
server_zero_dep.SniperHandler.handle_api_status(d)
