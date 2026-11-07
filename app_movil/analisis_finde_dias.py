import os, sys, datetime
import pandas as pd

sys.path.append(r"C:\Users\victo\nuevas_ruletas")
from bot_nuevas_ruletas import RULETAS_CONFIG, get_history_series

active_configs = {k: v for k, v in RULETAS_CONFIG.items() if v.get("active", False)}

events = []
for r_name, cfg in active_configs.items():
    nums, df = get_history_series(r_name)
    if df.empty or len(nums) < 40:
        continue
    lags = cfg["lags"]
    rec_w = cfg.get("rec_w", 6)
    use_anti = cfg.get("anti_clustering", False)
    blacklist = set(cfg.get("blacklist", []))
    target_streaks = cfg.get("target_streaks", [1])
    payout = cfg["payout"]
    markov = cfg.get("markov", {})
    
    min_k = max(max(lags), rec_w) + 1
    streak = 0
    cur_d = None
    seen_today = set()
    prev_was_repeat = False
    
    for i in range(min_k, len(df)):
        actual = str(nums[i]).strip()
        row = df.iloc[i]
        d = str(row["fecha"])
        if d != cur_d:
            cur_d = d
            seen_today = set()
            prev_was_repeat = False
            
        rec_set = set(str(n).strip() for n in nums[i - rec_w : i])
        raw_cands = [str(nums[i - l]).strip() for l in lags if i - l >= 0]
        cands_lag = sorted(list((set(raw_cands) - rec_set) - blacklist))
        
        last_num = str(nums[i - 1]).strip()
        m_cand = markov.get(last_num)
        if m_cand: m_cand = str(m_cand).strip()
        is_markov = bool(m_cand and m_cand not in rec_set and m_cand not in blacklist)
        
        skip_anti = bool(use_anti and prev_was_repeat)
        
        trigger = False
        cands_play = []
        if is_markov:
            trigger = True
            cands_play = [m_cand]
        elif streak in target_streaks and not skip_anti:
            trigger = True
            cands_play = cands_lag
            
        if trigger and cands_play:
            hit = (actual in cands_play)
            cost = len(cands_play)
            win_val = payout if hit else 0.0
            events.append({
                "fecha": d,
                "hora": row.get("hora", ""),
                "ruleta": r_name,
                "cands": cands_play,
                "actual": actual,
                "hit": hit,
                "cost": cost,
                "win": win_val,
                "pnl": win_val - cost
            })
            
        if cands_lag:
            hit_track = (actual in cands_lag)
            streak = 0 if hit_track else streak + 1
            
        seen_today.add(actual)
        prev_was_repeat = (actual in seen_today)

df_ev = pd.DataFrame(events)
def parse_time(h_str):
    try:
        return datetime.datetime.strptime(h_str.strip(), "%I:%M %p").time()
    except Exception:
        return datetime.time(0, 0)

df_ev['hora_t'] = df_ev['hora'].apply(parse_time)
df_ev = df_ev.sort_values(by=['fecha', 'hora_t']).reset_index(drop=True)

df_viernes = df_ev[df_ev['fecha'] >= '2026-10-30'].copy()

print("=== BALANCE POR DIA DESDE EL VIERNES 30 DE OCTUBRE ===")
for fecha, group in df_viernes.groupby('fecha'):
    total_ops = len(group)
    hits = len(group[group['hit'] == True])
    misses = total_ops - hits
    fichas = group['cost'].sum()
    cobrado = group['win'].sum()
    pnl = group['pnl'].sum()
    print(f"Fecha: {fecha} | Disparos: {total_ops:02d} | Hits: {hits} | Fallos: {misses:02d} | Fichas: {fichas} | PnL: {pnl:+,.1f} U")

print("\n=== TOTAL ACUMULADO DESDE EL VIERNES ===")
print(f"Total Disparos Generados: {len(df_viernes)}")
print(f"Aciertos (Hits): {len(df_viernes[df_viernes['hit'] == True])}")
print(f"Total Fallos: {len(df_viernes[df_viernes['hit'] == False])}")
print(f"Total Fichas Invertidas: {df_viernes['cost'].sum()}")
print(f"Total PnL en Unidades: {df_viernes['pnl'].sum():+,.1f}")
print(f"Total PnL en Bs (a Bs 100 por ficha): Bs {df_viernes['pnl'].sum() * 100:+,.2f}")
