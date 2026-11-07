import os
import sys
import pandas as pd
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(r"C:\Users\victo\nuevas_ruletas")
from config import RULETAS_CONFIG

# Let's inspect draw by draw for today
print("=" * 80)
print("AUDITORÍA DE CONDICIONES Y DISPAROS DE HOY (2026-11-05)")
print("=" * 80)

for r_name, cfg in RULETAS_CONFIG.items():
    if not cfg.get("active", False):
        continue
    fpath = cfg["file"]
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
    
    today_records = []
    
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
        
        # Markov
        cands_markov = []
        if str(last_num) in markov_snipers:
            tgt = str(markov_snipers[str(last_num)])
            if tgt not in rec_set and tgt not in blacklist:
                cands_markov = [tgt]
                
        # Mirror
        cands_mirror = []
        if str(last_num) in mirror_pairs:
            tgt_m = str(mirror_pairs[str(last_num)])
            if tgt_m not in rec_set and tgt_m not in blacklist:
                cands_mirror = [tgt_m]
                
        is_repeat_now = (actual in seen_today)
        skip_anti = bool(use_anti and prev_was_repeat)
        
        is_markov_active = len(cands_markov) > 0
        is_mirror_active = len(cands_mirror) > 0 and not is_markov_active
        
        qualifies = False
        tipo = ""
        cands_final = []
        
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
            tipo = f"RACHA_{streak}"
            qualifies = True
            
        hit_lag = (actual in cands_lag) if cands_lag else False
        
        # If today
        if d == "2026-11-05":
            today_records.append({
                "hora": h,
                "salido": actual,
                "streak_antes": streak,
                "cands_lag": cands_lag,
                "qualifies": qualifies,
                "tipo": tipo,
                "cands_final": cands_final,
                "hit": (actual in cands_final) if qualifies else False,
                "skip_anti": skip_anti,
                "is_rep": is_repeat_now
            })
            
        # Update streak
        if cands_lag and not skip_anti:
            streak = 0 if hit_lag else streak + 1
        elif cands_lag and skip_anti:
            streak = 0 if hit_lag else streak + 1
            
        seen_today.add(actual)
        prev_was_repeat = is_repeat_now
        
    print(f"\n>>> {r_name} (Target Streaks: {target_streaks}) <<<")
    for r in today_records:
        disp_txt = f"🚨 DISPARÓ [{r['tipo']}] -> Cands: {r['cands_final']} | Salido: #{r['salido']} | {'GANÓ' if r['hit'] else 'FALLÓ'}" if r['qualifies'] else f"NO DISPARÓ (Racha={r['streak_antes']}) | Salido: #{r['salido']} | Cands_lag: {len(r['cands_lag'])}"
        if r['skip_anti']:
            disp_txt += " [BLOQUEADO ANTI-CLUSTER]"
        print(f"   [{r['hora']}] {disp_txt}")
