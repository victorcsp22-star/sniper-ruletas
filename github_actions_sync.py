"""
Runner para GitHub Actions:
1. Extrae los ultimos resultados de tuAzar.com para las 7 ruletas oficiales.
2. Actualiza los historiales CSV y evalua las apuestas.
3. Genera live_radar.json y today_ledger.json en app_movil/static/.
"""
import os
import sys
import json
import datetime

# Asegurar path raiz
this_dir = os.path.dirname(os.path.abspath(__file__))
if this_dir not in sys.path:
    sys.path.insert(0, this_dir)

import app_movil.server_zero_dep as s

def run():
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}] Iniciando scrape de tuAzar...")
    live_data = s.parse_tuazar_results_pure()
    if not live_data:
        print("[!] No se obtuvieron datos de tuAzar.")
        return

    # Actualizar CSVs y evaluar
    counts = s.evaluate_and_update_all_pure(live_data)
    print(f"[*] Sorteos nuevos incorporados: {counts}")

    # Generar live_radar.json
    radar = {}
    for r_name in s.RULETAS:
        st, miss, info = s.get_current_streaks(r_name)
        cfg = s.RULETAS[r_name]
        target = cfg.get('target_streaks', [1])
        is_act = (st in target) and not info.get('is_anti_blocked', False) and len(info.get('cands', [])) > 0
        radar[r_name] = {
            'title': cfg['title'],
            'emoji': cfg['emoji'],
            'payout': cfg['payout'],
            'target_streaks': target,
            'racha': st,
            'misses': miss,
            'is_active': is_act,
            'candidatos': info.get('cands', []),
            'ultimo_str': info.get('last_str', '')
        }

    radar_path = os.path.join(s.STATIC_DIR, "live_radar.json")
    with open(radar_path, "w", encoding="utf-8") as f:
        json.dump(radar, f, ensure_ascii=False, indent=2)
    print(f"[OK] live_radar.json actualizado en {radar_path}")

    # Generar today_ledger.json
    items, summary = s.read_today_ledger()
    ledger_data = {"items": items, "summary": summary}
    ledger_path = os.path.join(s.STATIC_DIR, "today_ledger.json")
    with open(ledger_path, "w", encoding="utf-8") as f:
        json.dump(ledger_data, f, ensure_ascii=False, indent=2)
    print(f"[OK] today_ledger.json actualizado ({len(items)} operaciones)")

if __name__ == "__main__":
    run()
