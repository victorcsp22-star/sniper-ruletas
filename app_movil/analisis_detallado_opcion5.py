import os, sys, datetime
import pandas as pd
import numpy as np
from experimento_ampliacion import preloaded_data

# Extraer todos los eventos de la Opción 5 (4 Lags)
all_events = []

for r_name, d in preloaded_data.items():
    nums = d["nums"]
    dates = d["dates"]
    horas = d["horas"]
    base_lags = list(d["lags"])
    lags = base_lags + [base_lags[0] + 7]  # 4 Lags
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
            cost = len(cands_lag) * 1.0  # $1.00 USD plano por ficha
            premio = payout if hit else 0.0
            all_events.append({
                "fecha": dt,
                "hora": h,
                "ruleta": r_name,
                "cands": cands_lag,
                "fichas": len(cands_lag),
                "cost": cost,
                "hit": hit,
                "win": premio,
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
df['fecha_dt'] = pd.to_datetime(df['fecha'])

# 1. Métricas de Fallos Consecutivos (Valles)
valles = []
cur_v = 0
for h in df['hit']:
    if h:
        valles.append(cur_v)
        cur_v = 0
    else:
        cur_v += 1
valles.append(cur_v)

# 2. Análisis por Día
dias_group = df.groupby('fecha')
dias_summary = []
for f, grp in dias_group:
    ops = len(grp)
    hits = len(grp[grp['hit'] == True])
    inv = grp['cost'].sum()
    cob = grp['win'].sum()
    pnl = grp['pnl'].sum()
    dias_summary.append({
        "fecha": f,
        "ops": ops,
        "hits": hits,
        "inv": inv,
        "cob": cob,
        "pnl": pnl
    })
df_dias = pd.DataFrame(dias_summary)

# 3. Análisis por Semana (Lunes a Domingo)
df['semana'] = df['fecha_dt'].dt.to_period('W-SUN').astype(str)
semanas_group = df.groupby('semana')
semanas_summary = []
for s, grp in semanas_group:
    ops = len(grp)
    hits = len(grp[grp['hit'] == True])
    inv = grp['cost'].sum()
    cob = grp['win'].sum()
    pnl = grp['pnl'].sum()
    semanas_summary.append({
        "semana": s,
        "ops": ops,
        "hits": hits,
        "inv": inv,
        "cob": cob,
        "pnl": pnl
    })
df_semanas = pd.DataFrame(semanas_summary)

print("="*90)
print("AUDITORIA PROFUNDA DE LA OPCIÓN 5: 4 REZAGADOS (+1 LAG AUXILIAR) - $1.00 USD PLANO")
print("="*90)

print("\n--- 1. METRICAS GLOBALES Y COMPORTAMIENTO DE FALLOS ---")
print(f"• Total Operaciones:          {len(df):,}")
print(f"• Total Aciertos (Hits):      {len(df[df['hit']==True]):,} (Win Rate: {len(df[df['hit']==True])/len(df)*100:.2f}%)")
print(f"• Fichas / Disparo Promedio:  {df['fichas'].mean():.2f} fichas por jugada")
print(f"• Inversión Total:            ${df['cost'].sum():,.2f} USD (Bs {df['cost'].sum()*100:,.2f})")
print(f"• Cobrado Total:              ${df['win'].sum():,.2f} USD (Bs {df['win'].sum()*100:,.2f})")
print(f"• Beneficio Neto Total:       +${df['pnl'].sum():,.2f} USD (Bs +{df['pnl'].sum()*100:,.2f})")
print(f"• Retorno sobre Inversión:    +{df['pnl'].sum()/df['cost'].sum()*100:.2f}%")
print(f"• Valle Promedio entre Hits:  {np.mean(valles):.1f} fallos seguidos (Mediana: {np.median(valles):.1f} fallos)")
print(f"• Racha Máxima de Fallos:     {max(valles)} fallos seguidos")
cum = df['pnl'].cumsum()
peak = cum.cummax()
max_dd = (cum - peak).min()
print(f"• Drawdown Máximo Histórico:  -${abs(max_dd):,.2f} USD (-{abs(max_dd):,.0f} fichas)")

print("\n--- 2. RADIOGRAFIA DE DÍAS (BUENOS VS MALOS) ---")
tot_dias = len(df_dias)
dias_ganadores = len(df_dias[df_dias['pnl'] > 0])
dias_perdedores = len(df_dias[df_dias['pnl'] < 0])
dias_tablas = len(df_dias[df_dias['pnl'] == 0])

print(f"• Total Días Operados:        {tot_dias} días")
print(f"• Días Ganadores (Verdes):    {dias_ganadores} días ({dias_ganadores/tot_dias*100:.1f}%)")
print(f"• Días Perdedores (Rojos):    {dias_perdedores} días ({dias_perdedores/tot_dias*100:.1f}%)")
print(f"• Ganancia Promedio Día Verde: +${df_dias[df_dias['pnl'] > 0]['pnl'].mean():,.2f} USD (+Bs {df_dias[df_dias['pnl'] > 0]['pnl'].mean()*100:,.2f})")
print(f"• Pérdida Promedio Día Rojo:   -${abs(df_dias[df_dias['pnl'] < 0]['pnl'].mean()):,.2f} USD (-Bs {abs(df_dias[df_dias['pnl'] < 0]['pnl'].mean())*100:,.2f})")
print(f"• Mejor Día Histórico:         +${df_dias['pnl'].max():,.2f} USD ({df_dias.loc[df_dias['pnl'].idxmax()]['fecha']} con {df_dias.loc[df_dias['pnl'].idxmax()]['hits']} hits)")
print(f"• Peor Día Histórico:          -${abs(df_dias['pnl'].min()):,.2f} USD ({df_dias.loc[df_dias['pnl'].idxmin()]['fecha']} con 0 hits)")

print("\nTOP 5 MEJORES DÍAS:")
for idx, r in df_dias.sort_values(by='pnl', ascending=False).head(5).iterrows():
    print(f"  * {r['fecha']}: Ops: {r['ops']:2d} | Hits: {r['hits']} | Inv: ${r['inv']:<4.0f} | Cob: ${r['cob']:<4.0f} | PnL: +${r['pnl']:<5.1f} USD (+Bs {r['pnl']*100:,.2f})")

print("\nTOP 5 PEORES DÍAS:")
for idx, r in df_dias.sort_values(by='pnl', ascending=True).head(5).iterrows():
    print(f"  * {r['fecha']}: Ops: {r['ops']:2d} | Hits: {r['hits']} | Inv: ${r['inv']:<4.0f} | Cob: ${r['cob']:<4.0f} | PnL: -${abs(r['pnl']):<5.1f} USD (-Bs {abs(r['pnl'])*100:,.2f})")

print("\n--- 3. RADIOGRAFIA DE SEMANAS (BUENAS VS MALAS) ---")
tot_semanas = len(df_semanas)
sem_ganadoras = len(df_semanas[df_semanas['pnl'] > 0])
sem_perdedoras = len(df_semanas[df_semanas['pnl'] < 0])
sem_tablas = len(df_semanas[df_semanas['pnl'] == 0])

print(f"• Total Semanas Evaluadas:    {tot_semanas} semanas (2 años)")
print(f"• Semanas Ganadoras (Verdes): {sem_ganadoras} semanas ({sem_ganadoras/tot_semanas*100:.1f}%)")
print(f"• Semanas Perdedoras (Rojas): {sem_perdedoras} semanas ({sem_perdedoras/tot_semanas*100:.1f}%)")
print(f"• Ganancia Promedio Sem Verde: +${df_semanas[df_semanas['pnl'] > 0]['pnl'].mean():,.2f} USD (+Bs {df_semanas[df_semanas['pnl'] > 0]['pnl'].mean()*100:,.2f})")
print(f"• Pérdida Promedio Sem Roja:   -${abs(df_semanas[df_semanas['pnl'] < 0]['pnl'].mean()):,.2f} USD (-Bs {abs(df_semanas[df_semanas['pnl'] < 0]['pnl'].mean())*100:,.2f})")
print(f"• Mejor Semana Histórica:      +${df_semanas['pnl'].max():,.2f} USD ({df_semanas.loc[df_semanas['pnl'].idxmax()]['semana']} con {df_semanas.loc[df_semanas['pnl'].idxmax()]['hits']} hits)")
print(f"• Peor Semana Histórica:       -${abs(df_semanas['pnl'].min()):,.2f} USD ({df_semanas.loc[df_semanas['pnl'].idxmin()]['semana']})")

print("\nTOP 5 MEJORES SEMANAS:")
for idx, r in df_semanas.sort_values(by='pnl', ascending=False).head(5).iterrows():
    print(f"  * Semana {r['semana']}: Ops: {r['ops']:2d} | Hits: {r['hits']} | Inv: ${r['inv']:<5.0f} | Cob: ${r['cob']:<5.0f} | PnL: +${r['pnl']:<6.1f} USD (+Bs {r['pnl']*100:,.2f})")

print("\nTOP 5 PEORES SEMANAS:")
for idx, r in df_semanas.sort_values(by='pnl', ascending=True).head(5).iterrows():
    print(f"  * Semana {r['semana']}: Ops: {r['ops']:2d} | Hits: {r['hits']} | Inv: ${r['inv']:<5.0f} | Cob: ${r['cob']:<5.0f} | PnL: -${abs(r['pnl']):<6.1f} USD (-Bs {abs(r['pnl'])*100:,.2f})")
