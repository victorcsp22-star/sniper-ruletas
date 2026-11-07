import sys, os
sys.path.append(r"C:\Users\victo\nuevas_ruletas")
import bot_nuevas_ruletas as bot
import app_movil.server_zero_dep as srv

print("=== COMPARACION DE CONFIGURACIONES DE RULETAS ===")
bot_ruletas = bot.RULETAS_CONFIG
srv_ruletas = srv.RULETAS

for r_name in srv_ruletas:
    print(f"\n[Ruleta: {r_name}]")
    if r_name not in bot_ruletas:
        print(f"[-] NO EXISTE EN bot_nuevas_ruletas.py!")
        continue
    b_cfg = bot_ruletas[r_name]
    s_cfg = srv_ruletas[r_name]
    
    diffs = []
    for k in ["lags", "target_streaks", "wr_optimos", "rec_w", "anti_clustering", "blacklist", "markov", "payout"]:
        b_val = b_cfg.get(k)
        s_val = s_cfg.get(k)
        if b_val != s_val:
            diffs.append((k, b_val, s_val))
            
    if diffs:
        print("  DIFERENCIAS DETECTADAS:")
        for k, bv, sv in diffs:
            print(f"    * {k}:")
            print(f"        bot: {bv}")
            print(f"        srv: {sv}")
    else:
        print("  CONFIGURACION EXACTAMENTE IDENTICA.")
