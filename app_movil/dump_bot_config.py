import sys
sys.path.append(r'C:\Users\victo\nuevas_ruletas')
import bot_nuevas_ruletas as bot

print("=== CONFIGURACION MAESTRA DEL BOT GANADOR (bot_nuevas_ruletas.py) ===")
for k, v in bot.RULETAS_CONFIG.items():
    if v.get('active', False):
        print(f"[{k}]")
        print(f"   lags: {v.get('lags')}")
        print(f"   target_streaks: {v.get('target_streaks')}")
        print(f"   rec_w: {v.get('rec_w', 6)}")
        print(f"   anti_clustering: {v.get('anti_clustering', False)}")
        print(f"   blacklist: {v.get('blacklist', [])}")
        print(f"   payout: {v.get('payout')}")
        print(f"   file: {v.get('file')}")
