import os
import sys

# Agregar ruta raiz
this_dir = os.path.dirname(os.path.abspath(__file__))
if this_dir not in sys.path:
    sys.path.insert(0, this_dir)

from app_movil.server_zero_dep import ThreadingHTTPServer, SniperHandler, start_background_auto_sync

if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    port = int(os.environ.get("PORT", 10000))
    print(f"[*] Iniciando Sniper Ruletas Cloud en puerto {port}...")
    start_background_auto_sync()
    server = ThreadingHTTPServer(("0.0.0.0", port), SniperHandler)
    server.serve_forever()
