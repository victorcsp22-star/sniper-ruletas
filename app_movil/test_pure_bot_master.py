import os, sys
import pandas as pd

sys.path.append(r"C:\Users\victo\nuevas_ruletas")
import bot_nuevas_ruletas as bot

# Probar la simulación con la configuración EXACTA del bot maestro
configs = bot.RULETAS_CONFIG

all_events = []
for r_name, cfg in configs.items():
    if not cfg.get("active", False): continue
    nums, df = bot.get_history_series(r_name)
    if df.empty or len(nums) < 50: continue
    
    lags = cfg["lags"]
    rec_w = cfg.get("rec_w", 6)
    use_anti = cfg.get("anti_clustering", False)
    blacklist = set(str(x).strip().lstrip("0") or "0" for x in cfg.get("blacklist", []))
    target_streaks = cfg.get("target_streaks", [1])
    payout = cfg["payout"]
    
    nums_str = [str(x).strip().lstrip("0") or "0" for x in nums]
    dates = df["fecha"].astype(str).tolist()
    horas = df["hora"].astype(str).tolist() if "hora" in df.columns else [""] * len(df)
    
    min_k = max(max(lags), rec_w) + 1
    streak = 0
    cur_d = None
    seen_today = set()
    prev_was_repeat = False
    
    for i in range(min_k, len(nums_str)):
        act = nums_str[i]
        d = dates[i]
        h = horas[i]
        
        if d != cur_d:
            cur_d = d
            seen_today = set()
            prev_was_repeat = False
            
        rec_set = set(nums_str[i - rec_w : i])
        raw_cands = [nums_str[i - l] for l in lags if i - l >= 0]
        cands_lag = sorted(list((set(raw_cands) - rec_set) - blacklist))
        
        skip_anti = bool(use_anti and prev_was_repeat)
        trigger = (streak in target_streaks) and (not skip_anti) and (len(cands_lag) > 0)
        
        if trigger:
            hit = (act in cands_lag)
            cost = len(cands_lag)
            win_val = payout if hit else 0.0
            all_events.append({
                "fecha": d,
                "hora": h,
                "ruleta": r_name,
                "cands": cands_lag,
                "cost": cost,
                "act": act,
                "hit": hit,
                "pnl": win_val - cost
            })
            
        if cands_lag:
            hit_l = (act in cands_lag)
            streak = 0 if hit_l else streak + 1
            
        is_rep = (act in seen_today)
        seen_today.add(act)
        prev_was_repeat = is_rep

df_ev = pd.DataFrame(all_events)
print("=== RENDIMIENTO TOTAL CON MOTOR MAESTRO PURO (SIN MARKOV) ===")
ops = len(df_ev)
hits = len(df_ev[df_ev['hit'] == True])
wr = (hits / ops * 100) if ops > 0 else 0
cost = df_ev['cost'].sum()
pnl = df_ev['pnl'].sum()
roi = (pnl / cost * 100) if cost > 0 else 0
print(f"Total Ops: {ops}")
print(f"Total Hits: {hits} (Win Rate: {wr:.2f}%)")
print(f"Total Invertido: {cost:,.0f} U (Bs {cost*100:,.2f})")
print(f"Total PnL: {pnl:+,.0f} U (Bs {pnl*100:+,.2f})")
print(f"ROI: {roi:+.2f}%")

# Rendimiento hoy 2 de nov y ayer 1 de nov
for f in ["2026-11-01", "2026-11-02"]:
    sub = df_ev[df_ev['fecha'] == f]
    sub_ops = len(sub)
    sub_hits = len(sub[sub['hit'] == True])
    sub_pnl = sub['pnl'].sum()
    print(f"\nFecha {f}: {sub_ops} disparos | {sub_hits} hits | PnL: {sub_pnl:+.1f} U (Bs {sub_pnl*100:+,.2f})")
