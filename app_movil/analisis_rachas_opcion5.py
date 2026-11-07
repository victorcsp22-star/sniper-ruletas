import os, sys, datetime
import pandas as pd
import numpy as np
from experimento_ampliacion import preloaded_data

# Construir eventos de Opción 5 (4 Lags)
all_events = []
for r_name, d in preloaded_data.items():
    nums = d["nums"]
    dates = d["dates"]
    horas = d["horas"]
    base_lags = list(d["lags"])
    lags = base_lags + [base_lags[0] + 7]
    target_stk = d["target_stk"]
    rec_w = d["rec_w"]
    use_anti = d["use_anti"]
    blacklist = d["blacklist"]
    payout = d["payout"]
    
    min_k = max(max(lags), rec_w) + 1
    streak = 0
    cur_d = None
    seen_today = set()
    prev_was_repeat = False
    
    for i in range(min_k, len(nums)):
        act = nums[i]
        dt = dates[i]
        h = horas[i]
        if dt != cur_d:
            cur_d = dt
            seen_today = set()
            prev_was_repeat = False
            
        rec_set = set(nums[i - rec_w : i])
        raw_cands = [nums[i - l] for l in lags if i - l >= 0]
        cands_lag = sorted(list((set(raw_cands) - rec_set) - blacklist))
        skip_anti = bool(use_anti and prev_was_repeat)
        trigger = (streak in target_stk) and (not skip_anti) and (len(cands_lag) > 0)
        
        if trigger:
            hit = (act in cands_lag)
            cost = len(cands_lag) * 1.0
            premio = payout if hit else 0.0
            all_events.append({
                "fecha": dt,
                "hora": h,
                "ruleta": r_name,
                "cands": cands_lag,
                "fichas": len(cands_lag),
                "hit": hit,
                "pnl": premio - cost
            })
            
        if cands_lag and not skip_anti:
            hit_core = (act in cands_lag)
            streak = 0 if hit_core else streak + 1
        elif cands_lag and skip_anti:
            hit_core = (act in cands_lag)
            streak = 0 if hit_core else streak + 1
            
        is_rep = (act in seen_today)
        seen_today.add(act)
        prev_was_repeat = is_rep

df = pd.DataFrame(all_events)
def parse_time(h_str):
    try:
        return datetime.datetime.strptime(str(h_str).strip(), "%I:%M %p").time()
    except Exception:
        return datetime.time(0, 0)

df['hora_t'] = df['hora'].apply(parse_time)
df = df.sort_values(by=['fecha', 'hora_t']).reset_index(drop=True)

# 1. Extraer todas las rachas de fallos consecutivas y sus fechas/costos
rachas_fallos = []
cur_fallos = 0
cur_fichas_perdidas = 0
start_idx = 0

for i, row in df.iterrows():
    if row['hit']:
        if cur_fallos > 0:
            rachas_fallos.append({
                "longitud": cur_fallos,
                "fichas_perdidas": cur_fichas_perdidas,
                "fecha_inicio": df.loc[start_idx, 'fecha'],
                "fecha_fin": df.loc[i-1, 'fecha']
            })
        cur_fallos = 0
        cur_fichas_perdidas = 0
        start_idx = i + 1
    else:
        cur_fallos += 1
        cur_fichas_perdidas += row['fichas']

# Si termina en racha de fallos
if cur_fallos > 0:
    rachas_fallos.append({
        "longitud": cur_fallos,
        "fichas_perdidas": cur_fichas_perdidas,
        "fecha_inicio": df.loc[start_idx, 'fecha'],
        "fecha_fin": df.iloc[-1]['fecha']
    })

df_rf = pd.DataFrame(rachas_fallos)

# 2. Extraer rachas de aciertos (hits consecutivos o espaciados en menos de 3 tiros)
rachas_hits = []
cur_hits = 0
for h in df['hit']:
    if h:
        cur_hits += 1
    else:
        if cur_hits > 0:
            rachas_hits.append(cur_hits)
        cur_hits = 0
if cur_hits > 0:
    rachas_hits.append(cur_hits)

# 3. Distribución por tramos de rachas de fallos
tramos = [
    ("1 a 5 fallos (Valle muy corto)", (df_rf['longitud'] >= 1) & (df_rf['longitud'] <= 5)),
    ("6 a 10 fallos (Valle normal)", (df_rf['longitud'] >= 6) & (df_rf['longitud'] <= 10)),
    ("11 a 20 fallos (Valle medio)", (df_rf['longitud'] >= 11) & (df_rf['longitud'] <= 20)),
    ("21 a 40 fallos (Valle severo)", (df_rf['longitud'] >= 21) & (df_rf['longitud'] <= 40)),
    ("Más de 40 fallos (Estrés extremo)", (df_rf['longitud'] > 40)),
]

print("="*90)
print("AUDITORIA DETALLADA DE RACHAS (OPCIÓN 5: 4 REZAGADOS - 2 AÑOS DE HISTORIAL)")
print("="*90)

print(f"Total ciclos entre aciertos evaluados: {len(df_rf)}")
print(f"Longitud promedio de racha de fallos: {df_rf['longitud'].mean():.1f} fallos seguidos")
print(f"Mediana: {df_rf['longitud'].median():.1f} fallos")
print(f"Costo promedio de un valle: ${df_rf['fichas_perdidas'].mean():.2f} USD ({df_rf['fichas_perdidas'].mean():.1f} fichas)")

print("\n--- DISTRIBUCION DE PROBABILIDAD DE LOS VALLES DE FALLOS ---")
for nombre, cond in tramos:
    sub = df_rf[cond]
    pct = len(sub) / len(df_rf) * 100
    avg_loss = sub['fichas_perdidas'].mean() if len(sub) > 0 else 0
    print(f"• {nombre:<38}: {len(sub):3d} veces ({pct:5.1f}%) | Costo promedio: -${avg_loss:5.1f} USD")

print("\n--- TOP 10 PEORES RACHAS DE FALLOS DE LA HISTORIA (ESTRÉS DE BANCA) ---")
top_peores = df_rf.sort_values(by='longitud', ascending=False).head(10)
for idx, r in top_peores.iterrows():
    print(f"  * {r['longitud']:2d} fallos seguidos | Costo: -${r['fichas_perdidas']:4.0f} USD (-Bs {r['fichas_perdidas']*100:,.0f}) | Periodo: {r['fecha_inicio']} al {r['fecha_fin']}")

print("\n--- COMPORTAMIENTO DE LOS ACIERTOS (HITS) ---")
print(f"• Total Aciertos en 2 años: {df['hit'].sum()}")
print(f"• Aciertos consecutivos directos (back-to-back): {len([x for x in rachas_hits if x >= 2])} veces")
print(f"• Máxima racha de aciertos seguidos: {max(rachas_hits)} hits consecutivos")
print(f"• Veces que acertó 2 tiros seguidos: {rachas_hits.count(2)}")
print(f"• Veces que acertó 3 tiros seguidos: {rachas_hits.count(3)}")
