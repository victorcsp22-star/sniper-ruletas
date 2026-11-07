import sys
sys.path.append(r"C:\Users\victo\nuevas_ruletas")
import bot_nuevas_ruletas

print("CONFIGURACION OFICIAL BOT PC:")
for k, v in bot_nuevas_ruletas.RULETAS_CONFIG.items():
    if v.get("active"):
        print(f"[{k}]")
        print(f"  file: {v.get('file')}")
        print(f"  title: {v.get('title')}")
        print(f"  lags: {v.get('lags')}")
        print(f"  target_streaks: {v.get('target_streaks')}")
        print(f"  rec_w: {v.get('rec_w')}")
        print(f"  anti_clustering: {v.get('anti_clustering')}")
        print(f"  payout: {v.get('payout')}")
        print(f"  blacklist: {v.get('blacklist')}")
        print(f"  markov: {v.get('markov')}")
        print(f"  mirror: {v.get('mirror')}")
