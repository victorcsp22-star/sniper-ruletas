import os
import sys
import pandas as pd
import numpy as np

sys.path.append(r"C:\Users\victo\nuevas_ruletas")
from config import RULETAS_CONFIG

def extract_roulette_events(r_name, cfg):
    fpath = cfg["file"]
    if not os.path.exists(fpath):
        return []
    
    df = pd.read_csv(fpath, dtype={"numero": str})
    df["numero"] = df["numero"].astype(str).str.strip()
    df["dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
    df = df.dropna(subset=["dt"]).sort_values("dt").reset_index(drop=True)
    
    lags = cfg["lags"]
    rec_w = cfg.get("rec_w", 6)
    use_anti = cfg.get("anti_clustering", False)
    target_streaks = cfg.get("target_streaks", [1])
    payout = cfg["payout"]
    blacklist = set(cfg.get("blacklist", []))
    markov_snipers = cfg.get("markov_snipers", {})
    mirror_pairs = cfg.get("mirror_pairs", {})
    
    nums = df["numero"].tolist()
    dts = df["dt"].tolist()
    fechas = df["fecha"].tolist()
    horas = df["hora"].tolist()
    
    min_idx = max(lags) + max(rec_w, 8)
    
    streak = 0
    trigger_misses = 0
    seen_today = set()
    prev_date = None
    prev_was_repeat = False
    
    events = []
    
    for i in range(min_idx, len(nums)):
        actual = nums[i]
        d = fechas[i]
        h = horas[i]
        dt = dts[i]
        
        if d != prev_date:
            prev_date = d
            seen_today = set()
            prev_was_repeat = False
            
        last_num = nums[i-1]
        rec_set = set(nums[i-rec_w:i])
        raw_lags = [nums[i-l] for l in lags if i >= l]
        cands_lag = sorted(list((set(raw_lags) - rec_set) - blacklist))
        
        # Check Markov
        cands_markov = []
        if str(last_num) in markov_snipers:
            tgt = str(markov_snipers[str(last_num)])
            if tgt not in rec_set and tgt not in blacklist:
                cands_markov = [tgt]
                
        # Check Mirror
        cands_mirror = []
        if str(last_num) in mirror_pairs:
            tgt_m = str(mirror_pairs[str(last_num)])
            if tgt_m not in rec_set and tgt_m not in blacklist:
                cands_mirror = [tgt_m]
                
        is_repeat_now = (actual in seen_today)
        skip_anti = bool(use_anti and prev_was_repeat)
        
        # Determine if shot qualifies
        is_markov_active = len(cands_markov) > 0
        is_mirror_active = len(cands_mirror) > 0 and not is_markov_active
        
        cands_final = []
        tipo = ""
        qualifies = False
        
        if is_markov_active:
            cands_final = cands_markov
            tipo = "MARKOV"
            qualifies = True
        elif is_mirror_active:
            cands_final = cands_mirror
            tipo = "ESPEJO"
            qualifies = True
        elif cands_lag and not skip_anti and (streak in target_streaks):
            cands_final = cands_lag
            tipo = "LAG_RECOVERY"
            qualifies = True
            
        # Update streak for lag recovery
        if cands_lag and not skip_anti:
            hit_lag = (actual in cands_lag)
            if hit_lag:
                streak = 0
            else:
                streak += 1
        elif cands_lag and skip_anti:
            hit_lag = (actual in cands_lag)
            streak = 0 if hit_lag else streak + 1
            
        seen_today.add(actual)
        prev_was_repeat = is_repeat_now
        
        if qualifies and cands_final:
            hit = (actual in cands_final)
            events.append({
                "dt": dt,
                "fecha": d,
                "hora": h,
                "ruleta": r_name,
                "tipo": tipo,
                "candidatos": cands_final,
                "total_cands": len(cands_final),
                "actual": actual,
                "hit": hit,
                "payout": payout,
                "streak_at_trigger": streak,
                "trigger_misses": trigger_misses
            })
            if hit:
                trigger_misses = 0
            else:
                trigger_misses += 1
                
    return events

print("Extrayendo eventos de cada ruleta...")
all_events = []
for r_name, cfg in RULETAS_CONFIG.items():
    if not cfg.get("active", False):
        continue
    evs = extract_roulette_events(r_name, cfg)
    all_events.extend(evs)
    hits = sum(1 for e in evs if e["hit"])
    wr = (hits / len(evs) * 100) if evs else 0
    print(f"  {r_name:28} | Eventos: {len(evs):5} | Aciertos: {hits:4} | WR: {wr:5.2f}%")

print(f"Total eventos combinados en cartera: {len(all_events):,}")
