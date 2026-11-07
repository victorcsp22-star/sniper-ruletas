import os, sys, datetime
import pandas as pd
import numpy as np

sys.path.append(r"C:\Users\victo\nuevas_ruletas")
from bot_nuevas_ruletas import RULETAS_CONFIG, get_history_series, SIZING_MODEL, FIXED_STAKE_UNIT

print("Iniciando extracción determinista de todos los disparos históricos de las ruletas activas...")

# Ruletas activas (excluyendo Chaima si el usuario la quitó, o incluyendo las 9 oficiales)
# Verifiquemos con las 9 ruletas activas oficiales y también sin Loto Chaima
active_configs = {k: v for k, v in RULETAS_CONFIG.items() if v.get("active", False)}

all_events = []

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
    trigger_misses = 0
    cur_d = None
    seen_today = set()
    prev_was_repeat = False
    
    for i in range(min_k, len(df)):
        actual = nums[i]
        row = df.iloc[i]
        d = row["fecha"]
        
        if d != cur_d:
            cur_d = d
            seen_today = set()
            prev_was_repeat = False
            
        rec_set = set(nums[i - rec_w : i])
        raw_cands = [nums[i - l] for l in lags if i - l >= 0]
        cands_lag = sorted(list((set(raw_cands) - rec_set) - blacklist))
        skip_anti = bool(use_anti and prev_was_repeat)
        
        # Evaluar si hubo disparo en i-1 para este resultado en i
        last_num = nums[i-1]
        markov_cand = markov.get(last_num)
        is_markov = bool(markov_cand and markov_cand not in rec_set and markov_cand not in blacklist)
        
        cands_to_bet = []
        tipo = ""
        if is_markov:
            cands_to_bet = [markov_cand]
            tipo = "MARKOV"
        elif cands_lag and not skip_anti and (streak in target_streaks):
            cands_to_bet = cands_lag
            tipo = "REAGADOS"
            
        if cands_to_bet:
            hit = (actual in cands_to_bet)
            cost = len(cands_to_bet) * 1.0  # $1.00 USD fijo por ficha
            cobrado = (1.0 * payout) if hit else 0.0
            pnl = cobrado - cost
            all_events.append({
                "sort_dt": row["sort_dt"],
                "fecha": row["fecha"],
                "hora": row["hora"],
                "ruleta": r_name,
                "cands": cands_to_bet,
                "total_cands": len(cands_to_bet),
                "actual": actual,
                "hit": hit,
                "cost": cost,
                "cobrado": cobrado,
                "pnl": pnl,
                "tipo": tipo
            })
            
        # Actualizar racha interna del patrón
        if cands_lag and not skip_anti:
            hit_pattern = (actual in cands_lag)
            if streak in target_streaks:
                trigger_misses = 0 if hit_pattern else trigger_misses + 1
            streak = 0 if hit_pattern else streak + 1
        elif cands_lag and skip_anti:
            hit_pattern = (actual in cands_lag)
            streak = 0 if hit_pattern else streak + 1
            if streak in target_streaks:
                trigger_misses += 1
                
        is_rep = (actual in seen_today)
        seen_today.add(actual)
        prev_was_repeat = is_rep

events_df = pd.DataFrame(all_events).sort_values(by="sort_dt").reset_index(drop=True)
events_df["dt"] = pd.to_datetime(events_df["sort_dt"])
events_df["day_of_week"] = events_df["dt"].dt.day_name() # Monday, Tuesday...
events_df["is_weekend"] = events_df["dt"].dt.dayofweek.isin([5, 6]) # 5=Saturday, 6=Sunday

print(f"Total disparos históricos extraídos: {len(events_df)}")
print(f"Disparos de Lunes a Viernes (Semana): {len(events_df[~events_df['is_weekend']])}")
print(f"Disparos de Sábado y Domingo (Fin de semana): {len(events_df[events_df['is_weekend']])}")

# Análisis comparativo directo
def simular_cartera(df_ops, nombre):
    bankroll = 200.0
    peak = 200.0
    max_dd_usd = 0.0
    max_dd_pct = 0.0
    total_withdrawn = 0.0
    
    # Simular ciclo semanal de retiros (cada 7 días o retiro sobre $200)
    # También podemos medir PnL plano acumulado
    total_invested = df_ops["cost"].sum()
    total_collected = df_ops["cobrado"].sum()
    net_pnl = total_collected - total_invested
    wins = df_ops["hit"].sum()
    ops = len(df_ops)
    wr = (wins / ops * 100.0) if ops > 0 else 0.0
    roi = (net_pnl / total_invested * 100.0) if total_invested > 0 else 0.0
    
    # Calcular Max Drawdown y rachas de fallos consecutivas
    cur_consec_loss = 0
    max_consec_loss = 0
    loss_streaks = []
    
    cum_pnl = 0.0
    cum_peak = 0.0
    dd_list = []
    
    for _, row in df_ops.iterrows():
        p = row["pnl"]
        cum_pnl += p
        if cum_pnl > cum_peak:
            cum_peak = cum_pnl
        dd = cum_peak - cum_pnl
        if dd > max_dd_usd:
            max_dd_usd = dd
            
        if row["hit"]:
            if cur_consec_loss > 0:
                loss_streaks.append(cur_consec_loss)
                if cur_consec_loss > max_consec_loss:
                    max_consec_loss = cur_consec_loss
            cur_consec_loss = 0
        else:
            cur_consec_loss += 1
            
    if cur_consec_loss > 0:
        loss_streaks.append(cur_consec_loss)
        if cur_consec_loss > max_consec_loss:
            max_consec_loss = cur_consec_loss
            
    return {
        "nombre": nombre,
        "operaciones": ops,
        "victorias": wins,
        "win_rate_pct": round(wr, 2),
        "total_invertido": round(total_invested, 2),
        "total_cobrado": round(total_collected, 2),
        "pnl_neto": round(net_pnl, 2),
        "roi_pct": round(roi, 2),
        "max_drawdown_usd": round(max_dd_usd, 2),
        "max_fallos_consecutivos": max_consec_loss,
        "promedio_fallos_valle": round(np.mean(loss_streaks), 1) if loss_streaks else 0,
        "mediana_fallos_valle": np.median(loss_streaks) if loss_streaks else 0
    }

res_completo = simular_cartera(events_df, "1. Cartera Completa (Lunes a Domingo)")
res_sin_finde = simular_cartera(events_df[~events_df['is_weekend']], "2. Cartera Lunes a Viernes (SIN Sábados ni Domingos)")
res_solo_finde = simular_cartera(events_df[events_df['is_weekend']], "3. Solo Fines de Semana (Sábados y Domingos)")

print("\n" + "="*80)
print("RESULTADOS COMPARATIVOS FORMALES (2 AÑOS):")
print("="*80)
for r in [res_completo, res_sin_finde, res_solo_finde]:
    print(f"\n>>> {r['nombre']}")
    print(f"  • Operaciones: {r['operaciones']}")
    print(f"  • Aciertos: {r['victorias']} (Win Rate: {r['win_rate_pct']}%)")
    print(f"  • Total Invertido: ${r['total_invertido']:,.2f} USD")
    print(f"  • Total Cobrado:   ${r['total_cobrado']:,.2f} USD")
    print(f"  • PnL Neto:        ${r['pnl_neto']:,.2f} USD")
    print(f"  • ROI s/ Inversión: {r['roi_pct']}%")
    print(f"  • Drawdown Máximo: -${r['max_drawdown_usd']:,.2f} USD")
    print(f"  • Racha Máxima Fallos: {r['max_fallos_consecutivos']} fallos seguidos")
    print(f"  • Valle Promedio: {r['promedio_fallos_valle']} fallos (Mediana: {r['mediana_fallos_valle']})")
