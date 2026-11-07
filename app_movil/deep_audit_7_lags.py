import sys
sys.path.append(r'C:\Users\victo\nuevas_ruletas\app_movil')
import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict
import experimento_ampliacion as exp

preloaded_data = exp.preloaded_data

def deep_audit_7_lags():
    all_events = []
    
    for r_name, d in preloaded_data.items():
        nums = d["nums"]
        dates = d["dates"]
        horas = d["horas"]
        base_lags = list(d["lags"]) # 3 lags base
        
        # Generar 7 lags (+7, +12, +17, +22)
        step_offsets = [0, 7, 12, 17, 22]
        lags = list(base_lags)
        for k in range(1, 5):
            lags.append(base_lags[0] + step_offsets[k])
            
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
                cost = len(cands_play) * 1.0  # $1.00 USD por ficha
                premio = payout if hit else 0.0
                pnl = premio - cost
                all_events.append({
                    "fecha": dt,
                    "hora": hr,
                    "ruleta": r_name,
                    "cands": len(cands_play),
                    "cost": cost,
                    "hit": hit,
                    "premio": premio,
                    "pnl": pnl
                })
                
            if cands_lag:
                hit_core = (act in cands_lag)
                streak = 0 if hit_core else streak + 1
                
            is_rep = (act in seen_today)
            seen_today.add(act)
            prev_was_repeat = is_rep
            
    df = pd.DataFrame(all_events).sort_values(by=["fecha", "hora"]).reset_index(drop=True)
    
    # 1. Metricas Globales
    ops = len(df)
    hits = len(df[df['hit'] == True])
    wr = (hits / ops * 100)
    inv = df['cost'].sum()
    cob = df['premio'].sum()
    pnl = df['pnl'].sum()
    roi = (pnl / inv * 100)
    avg_fichas = inv / ops
    
    # Drawdown
    df['cum_pnl'] = df['pnl'].cumsum()
    df['peak'] = df['cum_pnl'].cummax()
    df['dd'] = df['cum_pnl'] - df['peak']
    max_dd = df['dd'].min()
    
    # Rachas de Fallos y Aciertos
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
    
    # 2. Desglose por Ruleta
    ruleta_stats = []
    for r, grp in df.groupby('ruleta'):
        r_ops = len(grp)
        r_hits = len(grp[grp['hit'] == True])
        r_wr = (r_hits / r_ops * 100)
        r_inv = grp['cost'].sum()
        r_pnl = grp['pnl'].sum()
        r_roi = (r_pnl / r_inv * 100)
        ruleta_stats.append({
            'ruleta': r,
            'ops': r_ops,
            'hits': r_hits,
            'wr': r_wr,
            'inv': r_inv,
            'pnl': r_pnl,
            'roi': r_roi
        })
    df_ruletas = pd.DataFrame(ruleta_stats).sort_values(by='pnl', ascending=False)
    
    # 3. Desglose Diario
    dias_list = []
    for d, grp in df.groupby('fecha'):
        d_ops = len(grp)
        d_hits = len(grp[grp['hit'] == True])
        d_inv = grp['cost'].sum()
        d_cob = grp['premio'].sum()
        d_pnl = grp['pnl'].sum()
        dias_list.append({
            'fecha': d,
            'ops': d_ops,
            'hits': d_hits,
            'inv': d_inv,
            'cob': d_cob,
            'pnl': d_pnl
        })
    df_dias = pd.DataFrame(dias_list)
    tot_dias = len(df_dias)
    dias_pos = df_dias[df_dias['pnl'] > 0]
    dias_neg = df_dias[df_dias['pnl'] < 0]
    dias_neu = df_dias[df_dias['pnl'] == 0]
    dias_con_hit = df_dias[df_dias['hits'] >= 1]
    
    # 4. Desglose Semanal
    df['fecha_dt'] = pd.to_datetime(df['fecha'])
    df['semana'] = df['fecha_dt'].dt.to_period('W-SUN')
    sem_list = []
    for s, grp in df.groupby('semana'):
        s_ops = len(grp)
        s_hits = len(grp[grp['hit'] == True])
        s_inv = grp['cost'].sum()
        s_cob = grp['premio'].sum()
        s_pnl = grp['pnl'].sum()
        sem_list.append({
            'semana': str(s),
            'ops': s_ops,
            'hits': s_hits,
            'inv': s_inv,
            'cob': s_cob,
            'pnl': s_pnl
        })
    df_sem = pd.DataFrame(sem_list)
    tot_sem = len(df_sem)
    sem_pos = df_sem[df_sem['pnl'] > 0]
    sem_neg = df_sem[df_sem['pnl'] < 0]
    sem_neu = df_sem[df_sem['pnl'] == 0]
    
    print("="*100)
    print("INFORME DE AUDITORIA CUANTITATIVA PROFUNDA: ESTRATEGIA 7 LAGS ($1.00 USD PLANO)")
    print("="*100)
    print(f"Total Operaciones Evaluadas:       {ops:,}")
    print(f"Total Aciertos (Hits):             {hits:,} (Win Rate: {wr:.2f}%)")
    print(f"Fichas Promedio por Disparo:       {avg_fichas:.2f} fichas")
    print(f"Capital Total Invertido:           ${inv:,.2f} USD (Bs {inv*100:,.2f})")
    print(f"Capital Total Cobrado:             ${cob:,.2f} USD (Bs {cob*100:,.2f})")
    print(f"Beneficio Neto Acumulado (PnL):    +${pnl:,.2f} USD (Bs +{pnl*100:,.2f})")
    print(f"Retorno sobre Inversion (ROI):     +{roi:.2f}%")
    print(f"Drawdown Maximo Historico:         -${abs(max_dd):,.2f} USD (-{abs(max_dd):.0f} fichas)")
    print(f"Profit Factor General:             {cob/inv:.2f}")
    
    print("\n" + "-"*100)
    print("ANALISIS ESTADISTICO DE RACHAS (COMPORTAMIENTO DE VALLES Y PICOS)")
    print("-"*100)
    print(f"Racha Maxima Historica de Fallos:  {max(fail_streaks)} fallos consecutivos")
    print(f"Valle Promedio entre Aciertos:     {np.mean(fail_streaks):.2f} fallos (Mediana: {np.median(fail_streaks):.1f} fallos)")
    print(f"Racha Maxima de Aciertos Seguidos: {max(hit_streaks)} aciertos seguidos")
    
    # Distribucion de fallos
    f_1_3 = len([f for f in fail_streaks if f <= 3])
    f_4_7 = len([f for f in fail_streaks if 4 <= f <= 7])
    f_8_12 = len([f for f in fail_streaks if 8 <= f <= 12])
    f_13_20 = len([f for f in fail_streaks if 13 <= f <= 20])
    f_gt_20 = len([f for f in fail_streaks if f > 20])
    tot_valleys = len(fail_streaks)
    
    print("\nDistribucion de Espera entre Aciertos (Valles):")
    print(f"  * 1 a 3 fallos:   {f_1_3:>4} veces ({f_1_3/tot_valleys*100:>5.1f}%) [Casi inmediato]")
    print(f"  * 4 a 7 fallos:   {f_4_7:>4} veces ({f_4_7/tot_valleys*100:>5.1f}%) [Espera tipica]")
    print(f"  * 8 a 12 fallos:  {f_8_12:>4} veces ({f_8_12/tot_valleys*100:>5.1f}%) [Espera moderada]")
    print(f"  * 13 a 20 fallos: {f_13_20:>4} veces ({f_13_20/tot_valleys*100:>5.1f}%) [Espera extendida]")
    print(f"  * Mas de 20 fallos: {f_gt_20:>2} veces ({f_gt_20/tot_valleys*100:>5.1f}%) [Racha anomala]")
    
    print("\n" + "-"*100)
    print("RADIOGRAFIA DIARIA (755 DIAS DE OPERACION)")
    print("-"*100)
    print(f"Dias con AL MENOS UN ACIERTO:      {len(dias_con_hit)} dias ({len(dias_con_hit)/tot_dias*100:.2f}%)")
    print(f"Dias en Blanco (0 aciertos):       {tot_dias - len(dias_con_hit)} dias ({(tot_dias - len(dias_con_hit))/tot_dias*100:.2f}%)")
    print(f"Dias Ganadores Netos (Verdes):     {len(dias_pos)} dias ({len(dias_pos)/tot_dias*100:.2f}%)")
    print(f"Dias Perdedores Netos (Rojos):     {len(dias_neg)} dias ({len(dias_neg)/tot_dias*100:.2f}%)")
    print(f"Ganancia Promedio Dia Verde:       +${dias_pos['pnl'].mean():.2f} USD (+Bs {dias_pos['pnl'].mean()*100:,.2f})")
    print(f"Perdida Promedio Dia Rojo:         -${abs(dias_neg['pnl'].mean()):.2f} USD (-Bs {abs(dias_neg['pnl'].mean())*100:,.2f})")
    print(f"Mejor Dia Historico:               +${dias_pos['pnl'].max():.2f} USD")
    print(f"Peor Dia Historico:                -${abs(dias_neg['pnl'].min()):.2f} USD")
    
    print("\n" + "-"*100)
    print("RADIOGRAFIA SEMANAL (111 SEMANAS / 2 ANOS)")
    print("-"*100)
    print(f"Semanas Ganadoras (Verdes):        {len(sem_pos)} semanas ({len(sem_pos)/tot_sem*100:.2f}%)")
    print(f"Semanas Perdedoras (Rojas):        {len(sem_neg)} semanas ({len(sem_neg)/tot_sem*100:.2f}%)")
    print(f"Ganancia Promedio Semana Verde:    +${sem_pos['pnl'].mean():.2f} USD (+Bs {sem_pos['pnl'].mean()*100:,.2f})")
    print(f"Perdida Promedio Semana Roja:      -${abs(sem_neg['pnl'].mean()):.2f} USD (-Bs {abs(sem_neg['pnl'].mean())*100:,.2f})")
    print(f"Mejor Semana Historica:            +${sem_pos['pnl'].max():.2f} USD (+Bs {sem_pos['pnl'].max()*100:,.2f})")
    print(f"Peor Semana Historica:             -${abs(sem_neg['pnl'].min()):.2f} USD (-Bs {abs(sem_neg['pnl'].min())*100:,.2f})")
    print(f"Profit Factor Semanal:             {sem_pos['pnl'].sum() / abs(sem_neg['pnl'].sum()):.2f}")
    
    print("\n" + "-"*100)
    print("DESGLOSE DE RENDIMIENTO POR CADA RULETA (7 LAGS)")
    print("-"*100)
    fmt_r = "{:<28} | {:<5} | {:<5} | {:<7} | {:<10} | {:<11} | {:<8}"
    print(fmt_r.format("RULETA", "OPS", "HITS", "WR%", "INVERSION", "PNL NETO", "ROI%"))
    print("-"*100)
    for idx, r in df_ruletas.iterrows():
        print(fmt_r.format(r['ruleta'], r['ops'], r['hits'], f"{r['wr']:.2f}%", f"${r['inv']:,.0f}", f"+${r['pnl']:,.1f}", f"{r['roi']:+.2f}%"))
    print("="*100)

if __name__ == '__main__':
    deep_audit_7_lags()
