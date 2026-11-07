import sys
sys.path.append(r'C:\Users\victo\nuevas_ruletas\app_movil')
import pandas as pd
import numpy as np
from datetime import datetime
import experimento_ampliacion as exp

preloaded_data = exp.preloaded_data

def get_detailed_metrics(n_lags):
    all_events = []
    step_offsets = [0, 7, 12, 17, 22, 27, 32, 37, 42, 47, 52]
    
    for r_name, d in preloaded_data.items():
        nums = d["nums"]
        dates = d["dates"]
        horas = d["horas"]
        base_lags = list(d["lags"])
        
        lags = list(base_lags)
        extra_needed = n_lags - 3
        if extra_needed > 0:
            for k in range(1, extra_needed + 1):
                offset = step_offsets[k] if k < len(step_offsets) else (k * 5)
                lags.append(base_lags[0] + offset)
        elif extra_needed < 0:
            lags = base_lags[:n_lags]
            
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
    
    # 1. Global
    ops = len(df)
    hits = len(df[df['hit'] == True])
    wr = hits / ops * 100
    inv = df['cost'].sum()
    cob = df['premio'].sum()
    pnl = df['pnl'].sum()
    roi = pnl / inv * 100
    avg_fichas = inv / ops
    profit_factor = cob / inv
    
    # Drawdown
    df['cum_pnl'] = df['pnl'].cumsum()
    df['peak'] = df['cum_pnl'].cummax()
    df['dd'] = df['cum_pnl'] - df['peak']
    max_dd = df['dd'].min()
    
    # Rachas de Fallos
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
    
    # Dias
    dias = []
    for d, grp in df.groupby('fecha'):
        d_hits = len(grp[grp['hit'] == True])
        d_pnl = grp['pnl'].sum()
        d_inv = grp['cost'].sum()
        d_cob = grp['premio'].sum()
        dias.append({'fecha': d, 'hits': d_hits, 'pnl': d_pnl, 'inv': d_inv, 'cob': d_cob})
    df_dias = pd.DataFrame(dias)
    tot_dias = len(df_dias)
    dias_hit = len(df_dias[df_dias['hits'] >= 1])
    dias_blanco = len(df_dias[df_dias['hits'] == 0])
    dias_verdes = len(df_dias[df_dias['pnl'] > 0])
    dias_rojos = len(df_dias[df_dias['pnl'] < 0])
    avg_dia_verde = df_dias[df_dias['pnl'] > 0]['pnl'].mean()
    avg_dia_rojo = abs(df_dias[df_dias['pnl'] < 0]['pnl'].mean())
    best_dia = df_dias['pnl'].max()
    worst_dia = abs(df_dias['pnl'].min())
    
    # Semanas
    df['fecha_dt'] = pd.to_datetime(df['fecha'])
    df['semana'] = df['fecha_dt'].dt.to_period('W-SUN')
    semanas = []
    for s, grp in df.groupby('semana'):
        s_hits = len(grp[grp['hit'] == True])
        s_pnl = grp['pnl'].sum()
        s_inv = grp['cost'].sum()
        s_cob = grp['premio'].sum()
        semanas.append({'semana': str(s), 'hits': s_hits, 'pnl': s_pnl, 'inv': s_inv, 'cob': s_cob})
    df_sem = pd.DataFrame(semanas)
    tot_sem = len(df_sem)
    sem_verdes = len(df_sem[df_sem['pnl'] > 0])
    sem_rojas = len(df_sem[df_sem['pnl'] < 0])
    avg_sem_verde = df_sem[df_sem['pnl'] > 0]['pnl'].mean()
    avg_sem_roja = abs(df_sem[df_sem['pnl'] < 0]['pnl'].mean())
    best_sem = df_sem['pnl'].max()
    worst_sem = abs(df_sem['pnl'].min())
    pf_semanal = df_sem[df_sem['pnl'] > 0]['pnl'].sum() / abs(df_sem[df_sem['pnl'] < 0]['pnl'].sum())
    
    return {
        'n_lags': n_lags,
        'ops': ops,
        'hits': hits,
        'wr': wr,
        'avg_fichas': avg_fichas,
        'inv': inv,
        'cob': cob,
        'pnl': pnl,
        'roi': roi,
        'max_dd': max_dd,
        'profit_factor': profit_factor,
        'fail_streaks': fail_streaks,
        'max_fail': max(fail_streaks),
        'avg_fail': np.mean(fail_streaks),
        'med_fail': np.median(fail_streaks),
        'tot_dias': tot_dias,
        'dias_hit': dias_hit,
        'pct_dias_hit': dias_hit / tot_dias * 100,
        'dias_blanco': dias_blanco,
        'pct_dias_blanco': dias_blanco / tot_dias * 100,
        'dias_verdes': dias_verdes,
        'pct_dias_verdes': dias_verdes / tot_dias * 100,
        'dias_rojos': dias_rojos,
        'pct_dias_rojos': dias_rojos / tot_dias * 100,
        'avg_dia_verde': avg_dia_verde,
        'avg_dia_rojo': avg_dia_rojo,
        'best_dia': best_dia,
        'worst_dia': worst_dia,
        'tot_sem': tot_sem,
        'sem_verdes': sem_verdes,
        'pct_sem_verdes': sem_verdes / tot_sem * 100,
        'sem_rojas': sem_rojas,
        'pct_sem_rojas': sem_rojas / tot_sem * 100,
        'avg_sem_verde': avg_sem_verde,
        'avg_sem_roja': avg_sem_roja,
        'best_sem': best_sem,
        'worst_sem': worst_sem,
        'pf_semanal': pf_semanal
    }

if __name__ == '__main__':
    m7 = get_detailed_metrics(7)
    m8 = get_detailed_metrics(8)
    
    print("="*90)
    print("COMPARATIVA TECNICA DETALLADA: 7 LAGS VS 8 LAGS ($1.00 USD PLANO / 2 ANOS)")
    print("="*90)
    print(f"{'METRICA OPERATIVA / PSICOLOGICA':<38} | {'7 LAGS':<22} | {'8 LAGS':<22}")
    print("-"*90)
    print(f"{'Total Operaciones':<38} | {m7['ops']:<22,d} | {m8['ops']:<22,d}")
    print(f"{'Total Aciertos (Hits)':<38} | {m7['hits']:<22,d} | {m8['hits']:<22,d}")
    print(f"{'Win Rate Global':<38} | {m7['wr']:>6.2f}%                | {m8['wr']:>6.2f}%")
    print(f"{'Fichas Promedio por Tiro':<38} | {m7['avg_fichas']:>6.2f} fichas           | {m8['avg_fichas']:>6.2f} fichas")
    print(f"{'Capital Total Invertido':<38} | ${m7['inv']:>10,.2f} USD         | ${m8['inv']:>10,.2f} USD")
    print(f"{'Capital Total Cobrado':<38} | ${m7['cob']:>10,.2f} USD         | ${m8['cob']:>10,.2f} USD")
    print(f"{'Beneficio Neto Acumulado (PnL)':<38} | +${m7['pnl']:>9,.2f} USD         | +${m8['pnl']:>9,.2f} USD")
    print(f"{'Retorno sobre Inversion (ROI)':<38} | +{m7['roi']:>5.2f}%               | +{m8['roi']:>5.2f}%")
    print(f"{'Drawdown Maximo Historico':<38} | -${abs(m7['max_dd']):>9.2f} USD         | -${abs(m8['max_dd']):>9.2f} USD")
    print(f"{'Profit Factor General':<38} | {m7['profit_factor']:>6.2f}                 | {m8['profit_factor']:>6.2f}")
    print("-"*90)
    print("ARMONIA Y RACHAS DE FALLOS:")
    print(f"{'Racha Maxima de Fallos':<38} | {m7['max_fail']:>2} fallos seguidos       | {m8['max_fail']:>2} fallos seguidos")
    print(f"{'Valle Promedio entre Hits':<38} | {m7['avg_fail']:>5.2f} fallos             | {m8['avg_fail']:>5.2f} fallos")
    print(f"{'Mediana de Espera (50% de hits)':<38} | {m7['med_fail']:>2.0f} fallos               | {m8['med_fail']:>2.0f} fallos")
    print("-"*90)
    print("COMPORTAMIENTO DIARIO (PAZ MENTAL):")
    print(f"{'Dias con AL MENOS 1 Cobro':<38} | {m7['dias_hit']}/{m7['tot_dias']} ({m7['pct_dias_hit']:.1f}%)       | {m8['dias_hit']}/{m8['tot_dias']} ({m8['pct_dias_hit']:.1f}%)")
    print(f"{'Dias en Blanco (0 cobros)':<38} | {m7['dias_blanco']}/{m7['tot_dias']} ({m7['pct_dias_blanco']:.1f}%)       | {m8['dias_blanco']}/{m8['tot_dias']} ({m8['pct_dias_blanco']:.1f}%)")
    print(f"{'Dias Verdes Netos (Ganancia)':<38} | {m7['dias_verdes']}/{m7['tot_dias']} ({m7['pct_dias_verdes']:.1f}%)       | {m8['dias_verdes']}/{m8['tot_dias']} ({m8['pct_dias_verdes']:.1f}%)")
    print(f"{'Ganancia Promedio Dia Verde':<38} | +${m7['avg_dia_verde']:>6.2f} USD            | +${m8['avg_dia_verde']:>6.2f} USD")
    print(f"{'Perdida Promedio Dia Rojo':<38} | -${m7['avg_dia_rojo']:>6.2f} USD            | -${m8['avg_dia_rojo']:>6.2f} USD")
    print(f"{'Mejor Dia Historico':<38} | +${m7['best_dia']:>6.2f} USD            | +${m8['best_dia']:>6.2f} USD")
    print(f"{'Peor Dia Historico':<38} | -${m7['worst_dia']:>6.2f} USD            | -${m8['worst_dia']:>6.2f} USD")
    print("-"*90)
    print("COMPORTAMIENTO SEMANAL (111 SEMANAS):")
    print(f"{'Semanas Ganadoras (Verdes)':<38} | {m7['sem_verdes']}/{m7['tot_sem']} ({m7['pct_sem_verdes']:.1f}%)         | {m8['sem_verdes']}/{m8['tot_sem']} ({m8['pct_sem_verdes']:.1f}%)")
    print(f"{'Semanas Perdedoras (Rojas)':<38} | {m7['sem_rojas']}/{m7['tot_sem']} ({m7['pct_sem_rojas']:.1f}%)         | {m8['sem_rojas']}/{m8['tot_sem']} ({m8['pct_sem_rojas']:.1f}%)")
    print(f"{'Ganancia Promedio Semana Verde':<38} | +${m7['avg_sem_verde']:>6.2f} USD           | +${m8['avg_sem_verde']:>6.2f} USD")
    print(f"{'Perdida Promedio Semana Roja':<38} | -${m7['avg_sem_roja']:>6.2f} USD            | -${m8['avg_sem_roja']:>6.2f} USD")
    print(f"{'Mejor Semana Historica':<38} | +${m7['best_sem']:>6.2f} USD           | +${m8['best_sem']:>6.2f} USD")
    print(f"{'Peor Semana Historica':<38} | -${m7['worst_sem']:>6.2f} USD           | -${m8['worst_sem']:>6.2f} USD")
    print(f"{'Profit Factor Semanal':<38} | {m7['pf_semanal']:>6.2f}                 | {m8['pf_semanal']:>6.2f}")
    print("="*90)
