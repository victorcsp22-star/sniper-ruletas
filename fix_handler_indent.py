import os

server_path = "C:/Users/victo/nuevas_ruletas/app_movil/server_zero_dep.py"
with open(server_path, "r", encoding="utf-8") as f:
    code = f.read()

# Locate get_30d_color_bubbles block
bubble_def = """def get_30d_color_bubbles(days_window=30):
    \"\"\"Calcula dinámicamente el rendimiento a 30 días de cada ruleta y asigna burbujas de color y stake.\"\"\"
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days_window)
    perf = {}
    for r_name, cfg in RULETAS.items():
        fpath = cfg.get("file", "")
        if not os.path.exists(fpath):
            fpath = get_ruleta_filepath(r_name)
        if not os.path.exists(fpath):
            continue
        try:
            records = read_csv_series(fpath)
            lags = cfg["lags"]
            rec_w = cfg["rec_w"]
            anti_clust = cfg.get("anti_clustering", False)
            payout = cfg["payout"]
            streaks = cfg.get("target_streaks", [1])
            
            streak = 0
            cost = 0.0
            rev = 0.0
            seen_today = set()
            last_f = None
            prev_rep = False
            
            min_i = max(lags) + rec_w
            for i in range(min_i, len(records)):
                rec = records[i]
                dt_str = rec.get("fecha", "") + " " + rec.get("hora", "")
                try:
                    dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d %I:%M %p")
                except Exception:
                    continue
                f = rec.get("fecha", "")
                act = rec.get("numero", "")
                if f != last_f:
                    seen_today = set()
                    last_f = f
                    prev_rep = False
                
                recent_window = [r["numero"] for r in records[i-rec_w:i]]
                rec_set = set(recent_window)
                raw = [records[i-l]["numero"] for l in lags if i>=l]
                cands = sorted(list(set(raw) - rec_set))
                cnt = len(cands)
                is_rep = (act in seen_today)
                skip = (anti_clust and prev_rep)
                hit = (act in cands) if cnt > 0 else False
                
                if dt >= cutoff and cnt > 0 and not skip:
                    if streak in streaks:
                        cost += cnt
                        if hit:
                            rev += payout
                    streak = 0 if hit else streak + 1
                elif cnt > 0 and skip:
                    streak = 0 if hit else streak + 1
                seen_today.add(act)
                prev_rep = is_rep
            perf[r_name] = rev - cost
        except Exception:
            perf[r_name] = 0.0
            
    sorted_r = sorted(perf.items(), key=lambda x: x[1], reverse=True)
    tiers = {}
    for rank, (r, pnl_val) in enumerate(sorted_r, 1):
        if rank <= 3:
            tiers[r] = {"rank": rank, "color": "VERDE", "emoji": "🟢", "stake": 1.50, "pnl_30d": round(pnl_val, 2), "color_hex": "#10b981", "badge": "🟢 $1.50"}
        elif rank <= 5:
            tiers[r] = {"rank": rank, "color": "AMARILLO", "emoji": "🟡", "stake": 1.00, "pnl_30d": round(pnl_val, 2), "color_hex": "#f59e0b", "badge": "🟡 $1.00"}
        else:
            tiers[r] = {"rank": rank, "color": "ROJO", "emoji": "🔴", "stake": 0.50, "pnl_30d": round(pnl_val, 2), "color_hex": "#ef4444", "badge": "🔴 $0.50"}
    return tiers"""

c_norm = code.replace("\r\n", "\n")
b_norm = bubble_def.replace("\r\n", "\n")

if b_norm in c_norm:
    # Remove from current position inside class
    c_norm = c_norm.replace(b_norm, "")
    # Place BEFORE class SniperHandler
    c_norm = c_norm.replace("class SniperHandler(SimpleHTTPRequestHandler):", b_norm + "\n\n\nclass SniperHandler(SimpleHTTPRequestHandler):")
    with open(server_path, "w", encoding="utf-8") as f:
        f.write(c_norm)
    print("Successfully moved get_30d_color_bubbles outside class SniperHandler.")
else:
    print("Error: bubble_def not found.")
