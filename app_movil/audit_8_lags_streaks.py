import sys
sys.path.append(r'C:\Users\victo\nuevas_ruletas\app_movil')
import pandas as pd
import numpy as np
from datetime import datetime
import experimento_ampliacion as exp

preloaded_data = exp.preloaded_data

def audit_streaks_and_weeks_8_lags():
    all_events = []
    step_offsets = [0, 7, 12, 17, 22, 27, 32, 37, 42, 47, 52]
    n_lags = 8
    
    for r_name, d in preloaded_data.items():
        nums = d["nums"]
        dates = d["dates"]
        horas = d["horas"]
        base_lags = list(d["lags"])
        
        lags = list(base_lags)
        extra_needed = n_lags - 3
        for k in range(1, extra_needed + 1):
            offset = step_offsets[k] if k < len(step_offsets) else (k * 5)
            lags.append(base_lags[0] + offset)
            
        target_stk = d["target_stk"]
        rec_w = d["rec_w"]
        use_anti = d["use_anti"]
        blacklist = d["blacklist"]
        payout = d["payout"]
        tot_terms = d["tot_terms"]
        
        min_k = max(max(lags), rec_w) + 1
        streak = 0
        cur_d = None
        seen_today = set()
        prev_was_repeat = False
        
        for i in range(min_k, len(nums)):
            act = nums[i]
            dt = dates[i]
            hr = horas[i]
            
            if dt != cur_d:
                cur_d = dt
                seen_today = set()
                prev_was_repeat = False
                
            rec_set = set(nums[i - rec_w : i])
            raw_cands = [nums[i - l] for l in lags if i - l >= 0]
            cands_lag = sorted(list((set(raw_cands) - rec_set) - blacklist))
            cands_play = cands_lag
            
            skip_anti = bool(use_anti and prev_was_repeat)
            trigger = (streak in target_stk) and (not skip_anti) and (len(cands_play) > 0)
            
            if trigger:
                hit = (act in cands_play)
                cost = len(cands_play) * 1.0  # $1.00 USD
                premio = payout if hit else 0.0
                all_events.append({
                    "fecha": dt,
                    "hora": hr,
                    "ruleta": r_name,
                    "cands": len(cands_play),
                    "cost": cost,
                    "hit": hit,
                    "premio": premio,
                    "pnl": premio - cost
                })
                
            if cands_lag:
                hit_core = (act in cands_lag)
                streak = 0 if hit_core else streak + 1
                
            is_rep = (act in seen_today)
            seen_today.add(act)
            prev_was_repeat = is_rep
            
    df = pd.DataFrame(all_events).sort_values(by=["fecha", "hora"]).reset_index(drop=True)
    
    # 1. Semanas
    df['fecha_dt'] = pd.to_datetime(df['fecha'])
    df['semana'] = df['fecha_dt'].dt.to_period('W-SUN')
    semanas = []
    for s, grp in df.groupby('semana'):
        s_hits = len(grp[grp['hit'] == True])
        s_pnl = grp['pnl'].sum()
        s_inv = grp['cost'].sum()
        s_cob = grp['premio'].sum()
        s_ops = len(grp)
        semanas.append({
            'semana': str(s),
            'ops': s_ops,
            'hits': s_hits,
            'inv': s_inv,
            'cob': s_cob,
            'pnl': s_pnl,
            'win': s_pnl > 0
        })
    df_sem = pd.DataFrame(semanas)
    tot_sem = len(df_sem)
    sem_verdes = len(df_sem[df_sem['pnl'] > 0])
    sem_rojas = len(df_sem[df_sem['pnl'] < 0])
    sem_neutras = len(df_sem[df_sem['pnl'] == 0])
    
    # Rachas de semanas ganadoras consecutivas vs perdedoras consecutivas
    streak_sem_w = []
    streak_sem_l = []
    cur_w = 0
    cur_l = 0
    for w in df_sem['win']:
        if w:
            cur_w += 1
            if cur_l > 0:
                streak_sem_l.append(cur_l)
                cur_l = 0
        else:
            cur_l += 1
            if cur_w > 0:
                streak_sem_w.append(cur_w)
                cur_w = 0
    if cur_w > 0: streak_sem_w.append(cur_w)
    if cur_l > 0: streak_sem_l.append(cur_l)
    
    # 2. Rachas de Disparos (Fallos consecutivos y Aciertos consecutivos)
    fail_streaks = []
    hit_streaks = []
    cur_fail = 0
    cur_hit = 0
    for h in df['hit']:
        if not h:
            cur_fail += 1
            if cur_hit > 0:
                hit_streaks.append(cur_hit)
                cur_hit = 0
        else:
            cur_hit += 1
            if cur_fail > 0:
                fail_streaks.append(cur_fail)
                cur_fail = 0
    if cur_fail > 0: fail_streaks.append(cur_fail)
    if cur_hit > 0: hit_streaks.append(cur_hit)
    
    print("="*90)
    print("ANALISIS PROFUNDO DE SEMANAS Y RACHAS EN ESTRATEGIA 8 LAGS")
    print("="*90)
    print(f"Total Semanas Evaluadas:               {tot_sem} semanas (2 aos)")
    print(f"Semanas Positivas (Verdes):            {sem_verdes} semanas ({sem_verdes/tot_sem*100:.2f}%)")
    print(f"Semanas Negativas (Rojas):             {sem_rojas} semanas ({sem_rojas/tot_sem*100:.2f}%)")
    print(f"Ganancia Promedio en Semana Verde:     +${df_sem[df_sem['pnl']>0]['pnl'].mean():.2f} USD (+Bs {df_sem[df_sem['pnl']>0]['pnl'].mean()*100:,.2f})")
    print(f"Perdida Promedio en Semana Roja:       -${abs(df_sem[df_sem['pnl']<0]['pnl'].mean()):.2f} USD (-Bs {abs(df_sem[df_sem['pnl']<0]['pnl'].mean())*100:,.2f})")
    print(f"Mejor Semana Historica:                +${df_sem['pnl'].max():.2f} USD (+Bs {df_sem['pnl'].max()*100:,.2f})")
    print(f"Peor Semana Historica:                 -${abs(df_sem['pnl'].min()):.2f} USD (-Bs {abs(df_sem['pnl'].min())*100:,.2f})")
    print(f"Racha Maxima de Semanas Verdes:        {max(streak_sem_w)} semanas consecutivas ganando")
    print(f"Racha Maxima de Semanas Rojas:         {max(streak_sem_l)} semanas consecutivas perdiendo")
    
    print("\n" + "-"*90)
    print("DETALLE COMPLETO DE RACHAS DE DISPAROS (FALLOS CONSECUTIVOS)")
    print("-"*90)
    print(f"Total Aciertos Registrados:            {len(df[df['hit']==True]):,}")
    print(f"Total Valles de Espera:                {len(fail_streaks):,}")
    print(f"Racha Maxima de Fallos Consecutivos:   {max(fail_streaks)} fallos seguidos")
    print(f"Valle Promedio de Fallos:              {np.mean(fail_streaks):.2f} fallos")
    print(f"Mediana de Fallos:                     {np.median(fail_streaks):.1f} fallos (el 50% de las veces cobras en <= 4 tiros)")
    print(f"Racha Maxima de Aciertos Seguidos:     {max(hit_streaks)} tiros cobrados al hilo")
    
    # Distribucion de fallos por tramos
    tot_v = len(fail_streaks)
    f_1_2 = len([f for f in fail_streaks if f <= 2])
    f_3_5 = len([f for f in fail_streaks if 3 <= f <= 5])
    f_6_10 = len([f for f in fail_streaks if 6 <= f <= 10])
    f_11_15 = len([f for f in fail_streaks if 11 <= f <= 15])
    f_16_20 = len([f for f in fail_streaks if 16 <= f <= 20])
    f_21_25 = len([f for f in fail_streaks if 21 <= f <= 25])
    f_gt_25 = len([f for f in fail_streaks if f > 25])
    
    print("\nDesglose de la Espera entre Cobros (Frecuencia de Valles):")
    print(f"  * 1 a 2 fallos (Cobro inmediato):        {f_1_2:>4} veces ({f_1_2/tot_v*100:>5.1f}%)")
    print(f"  * 3 a 5 fallos (Espera rapida tipica):   {f_3_5:>4} veces ({f_3_5/tot_v*100:>5.1f}%)")
    print(f"  * 6 a 10 fallos (Espera estandar):       {f_6_10:>4} veces ({f_6_10/tot_v*100:>5.1f}%)")
    print(f"  * 11 a 15 fallos (Racha fria moderada):  {f_11_15:>4} veces ({f_11_15/tot_v*100:>5.1f}%)")
    print(f"  * 16 a 20 fallos (Racha fria intensa):   {f_16_20:>4} veces ({f_16_20/tot_v*100:>5.1f}%)")
    print(f"  * 21 a 25 fallos (Racha infrecuente):    {f_21_25:>4} veces ({f_21_25/tot_v*100:>5.1f}%)")
    print(f"  * Mas de 25 fallos (Racha extrema rara): {f_gt_25:>4} veces ({f_gt_25/tot_v*100:>5.1f}%) [Maximo 32]")
    print("="*90)

if __name__ == '__main__':
    audit_streaks_and_weeks_8_lags()
