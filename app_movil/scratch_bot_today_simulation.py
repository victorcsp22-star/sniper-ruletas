import sys, os, datetime
import pandas as pd
sys.path.append(r"C:\Users\victo\nuevas_ruletas")
import bot_nuevas_ruletas
from bot_nuevas_ruletas import RULETAS_CONFIG, get_history_series

# Replicar exactamente la lógica de check_and_update del bot_nuevas_ruletas.py
# a lo largo de todo el día 2026-11-01 sorteo por sorteo

# 1. Obtener el estado previo a hoy (hasta el 2026-10-31 23:59)
# Calcular rachas y misses de cada ruleta al inicio de hoy
state_streaks = {}
state_misses = {}

for r_name, cfg in RULETAS_CONFIG.items():
    if not cfg.get("active", False): continue
    nums, df = get_history_series(r_name)
    df_prev = df[df["fecha"] < "2026-11-01"]
    
    lags = cfg["lags"]
    rec_w = cfg.get("rec_w", 6)
    use_anti = cfg.get("anti_clustering", False)
    blacklist = set(cfg.get("blacklist", []))
    target_streaks = cfg.get("target_streaks", [1])
    
    nums_prev = df_prev["numero"].tolist()
    stk = 0
    mss = 0
    cur_d = None
    seen_today = set()
    prev_was_repeat = False
    
    min_k = max(max(lags), rec_w) + 1
    for i in range(min_k, len(nums_prev)):
        actual = nums_prev[i]
        d = df_prev.iloc[i]["fecha"]
        if d != cur_d:
            cur_d = d
            seen_today = set()
            prev_was_repeat = False
        
        rec_set = set(nums_prev[i - rec_w : i])
        raw_cands = [nums_prev[i - l] for l in lags if i - l >= 0]
        cands_lag = sorted(list((set(raw_cands) - rec_set) - blacklist))
        skip_anti = bool(use_anti and prev_was_repeat)
        
        if cands_lag and not skip_anti:
            hit = (actual in cands_lag)
            if stk in target_streaks:
                mss = 0 if hit else mss + 1
            stk = 0 if hit else stk + 1
        elif cands_lag and skip_anti:
            hit = (actual in cands_lag)
            stk = 0 if hit else stk + 1
            if stk in target_streaks:
                mss += 1
                
        is_rep = (actual in seen_today)
        seen_today.add(actual)
        prev_was_repeat = is_rep
        
    state_streaks[r_name] = stk
    state_misses[r_name] = mss

print("ESTADO DE RACHAS AL INICIO DE HOY (00:00 AM):")
for k, v in state_streaks.items():
    print(f"  {k:26}: Racha={v}, Misses={state_misses[k]}")

# 2. Ahora reproducir el día de hoy paso a paso en el bot
# Para cada ruleta, recorrer los sorteos de hoy
bot_disparos_hoy = []

for r_name, cfg in RULETAS_CONFIG.items():
    if not cfg.get("active", False): continue
    nums, df = get_history_series(r_name)
    
    df_today = df[df["fecha"] == "2026-11-01"]
    if df_today.empty: continue
    
    lags = cfg["lags"]
    rec_w = cfg.get("rec_w", 6)
    use_anti = cfg.get("anti_clustering", False)
    blacklist = set(cfg.get("blacklist", []))
    target_streaks = cfg.get("target_streaks", [1])
    markov = cfg.get("markov", {})
    payout = cfg["payout"]
    
    stk = state_streaks[r_name]
    mss = state_misses[r_name]
    seen_today = set()
    prev_was_repeat = False
    
    for idx in df_today.index:
        actual = str(nums[idx]).strip()
        row = df.iloc[idx]
        hora = row["hora"]
        sort_dt = row["sort_dt"]
        
        past_nums = nums[:idx]
        rec_set = set(past_nums[-rec_w:])
        raw_cands = [past_nums[-l] for l in lags if l <= len(past_nums)]
        cands_lag = sorted(list((set(raw_cands) - rec_set) - blacklist))
        skip_anti = bool(use_anti and prev_was_repeat)
        
        # Evaluar disparo
        last_num = str(past_nums[-1]).strip() if past_nums else ""
        markov_cand = markov.get(last_num)
        is_markov = bool(markov_cand and markov_cand not in rec_set and markov_cand not in blacklist)
        
        # Verificar cuarentena
        is_quar = (mss >= 20)
        
        cands_to_bet = []
        tipo = ""
        if is_markov:
            cands_to_bet = [markov_cand]
            tipo = "MARKOV"
        elif cands_lag and not skip_anti and (stk in target_streaks) and not is_quar:
            cands_to_bet = cands_lag
            tipo = "REZAGADOS"
            
        if cands_to_bet:
            hit = (actual in cands_to_bet)
            cost = len(cands_to_bet) * 1.0
            cob = (1.0 * payout) if hit else 0.0
            pnl = cob - cost
            bot_disparos_hoy.append({
                "sort_dt": sort_dt,
                "fecha": "2026-11-01",
                "hora": hora,
                "ruleta": r_name,
                "cands": cands_to_bet,
                "tipo": tipo,
                "salido": f"[{actual}] {row['animal']}",
                "hit": hit,
                "cost": cost,
                "cobrado": cob,
                "pnl": pnl,
                "stk_en_disparo": stk,
                "mss_en_disparo": mss
            })
            
        # Actualizar racha tras el sorteo
        if cands_lag and not skip_anti:
            hit_pattern = (actual in cands_lag)
            if stk in target_streaks:
                mss = 0 if hit_pattern else mss + 1
            stk = 0 if hit_pattern else stk + 1
        elif cands_lag and skip_anti:
            hit_pattern = (actual in cands_lag)
            stk = 0 if hit_pattern else stk + 1
            if stk in target_streaks:
                mss += 1
                
        is_rep = (actual in seen_today)
        seen_today.add(actual)
        prev_was_repeat = is_rep

bot_df = pd.DataFrame(bot_disparos_hoy).sort_values(by="sort_dt").reset_index(drop=True)
print(f"\n================================================================================")
print(f"DISPAROS QUE EL MOTOR DEL BOT DETERMINÓ PARA HOY DOMINGO (TOTAL: {len(bot_df)})")
print(f"================================================================================")
for i, r in bot_df.iterrows():
    cond = "GANADA" if r["hit"] else "FALLO"
    print(f"#{i+1:02d} | {r['hora']:<8} | {r['ruleta']:<26} | Jugados: {r['cands']} ({r['tipo']}) | Salido: {r['salido']:<18} | Cost: ${r['cost']} | PnL: ${r['pnl']} ({cond})")

print(f"\nRESUMEN BOT DE LA PC HOY:")
print(f"  • Total disparos determinados por la lógica: {len(bot_df)}")
print(f"  • Aciertos: {bot_df['hit'].sum()}")
print(f"  • Fallos: {len(bot_df) - bot_df['hit'].sum()}")
print(f"  • Inversión Total: ${bot_df['cost'].sum():.2f} USD")
print(f"  • Cobrado Total:   ${bot_df['cobrado'].sum():.2f} USD")
print(f"  • PnL Neto:        ${bot_df['pnl'].sum():.2f} USD")
