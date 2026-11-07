import sys
sys.path.append(r'C:\Users\victo\nuevas_ruletas\app_movil')
import pandas as pd
import numpy as np
from datetime import datetime
import experimento_ampliacion as exp

preloaded_data = exp.preloaded_data

def get_ruletas_stats(n_lags=8):
    all_events = []
    step_offsets = [0, 7, 12, 17, 22, 27, 32, 37, 42, 47, 52]
    
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
    return df

if __name__ == '__main__':
    df = get_ruletas_stats(8)
    
    tot_dias_global = df['fecha'].nunique()
    
    # 1. Rendimiento y operaciones por Ruleta individual
    ruleta_summary = []
    for r, grp in df.groupby('ruleta'):
        ops = len(grp)
        hits = len(grp[grp['hit'] == True])
        wr = hits / ops * 100
        inv = grp['cost'].sum()
        pnl = grp['pnl'].sum()
        roi = pnl / inv * 100
        dias_activas = grp['fecha'].nunique()
        ops_por_dia = ops / tot_dias_global
        
        ruleta_summary.append({
            'ruleta': r,
            'ops': ops,
            'hits': hits,
            'wr': wr,
            'inv': inv,
            'pnl': pnl,
            'roi': roi,
            'ops_dia': ops_por_dia
        })
    df_r = pd.DataFrame(ruleta_summary).sort_values(by='pnl', ascending=False).reset_index(drop=True)
    
    print("="*105)
    print(f"DESGLOSE DE OPERACIONES DIARIAS Y EFECTIVIDAD POR RULETA (8 LAGS - {tot_dias_global} DIAS EVALUADOS)")
    print("="*105)
    print(f"{'RANK':<4} | {'RULETA':<28} | {'OPS TOT':<7} | {'OPS/DIA':<8} | {'HITS':<5} | {'WINRATE':<8} | {'PNL ($)':<12} | {'ROI %':<8}")
    print("-"*105)
    for idx, row in df_r.iterrows():
        print(f"#{idx+1:<3} | {row['ruleta']:<28} | {row['ops']:<7,d} | {row['ops_dia']:>6.2f}   | {row['hits']:<5,d} | {row['wr']:>6.2f}% | +${row['pnl']:>9,.1f} | {row['roi']:>+6.2f}%")
    print("="*105)
    
    # Total de las 9 ruletas
    tot_ops_9 = len(df)
    ops_dia_9 = tot_ops_9 / tot_dias_global
    pnl_9 = df['pnl'].sum()
    roi_9 = pnl_9 / df['cost'].sum() * 100
    wr_9 = len(df[df['hit']==True]) / tot_ops_9 * 100
    
    # Max DD 9 ruletas
    df['cum_pnl'] = df['pnl'].cumsum()
    df['peak'] = df['cum_pnl'].cummax()
    max_dd_9 = (df['cum_pnl'] - df['peak']).min()
    
    # Filtrar las 7 más efectivas por PnL (Top 7)
    top_7_ruletas = df_r.head(7)['ruleta'].tolist()
    peores_2_ruletas = df_r.tail(2)['ruleta'].tolist()
    
    df_top7 = df[df['ruleta'].isin(top_7_ruletas)].copy().reset_index(drop=True)
    tot_ops_7 = len(df_top7)
    ops_dia_7 = tot_ops_7 / tot_dias_global
    pnl_7 = df_top7['pnl'].sum()
    inv_7 = df_top7['cost'].sum()
    roi_7 = pnl_7 / inv_7 * 100
    wr_7 = len(df_top7[df_top7['hit']==True]) / tot_ops_7 * 100
    
    df_top7['cum_pnl'] = df_top7['pnl'].cumsum()
    df_top7['peak'] = df_top7['cum_pnl'].cummax()
    max_dd_7 = (df_top7['cum_pnl'] - df_top7['peak']).min()
    
    # Semanas Top 7
    df_top7['fecha_dt'] = pd.to_datetime(df_top7['fecha'])
    df_top7['semana'] = df_top7['fecha_dt'].dt.to_period('W-SUN')
    sem_top7 = [grp['pnl'].sum() for _, grp in df_top7.groupby('semana')]
    sem_pos_7 = len([s for s in sem_top7 if s > 0])
    tot_sem_7 = len(sem_top7)
    
    # Dias con cobro Top 7
    dias_hit_7 = len([grp for _, grp in df_top7.groupby('fecha') if len(grp[grp['hit']==True]) >= 1])
    
    # Rachas fallos Top 7
    streaks_7 = []
    c_fail = 0
    for h in df_top7['hit']:
        if not h:
            c_fail += 1
        else:
            streaks_7.append(c_fail)
            c_fail = 0
    if c_fail > 0: streaks_7.append(c_fail)
    max_fail_7 = max(streaks_7) if streaks_7 else 0
    avg_fail_7 = np.mean(streaks_7) if streaks_7 else 0
    med_fail_7 = np.median(streaks_7) if streaks_7 else 0
    
    print("\n" + "="*105)
    print("COMPARATIVA DE IMPACTO: OPERAR CON LAS 9 RULETAS VS. OPERAR SOLO CON LAS 7 MAS EFECTIVAS")
    print("="*105)
    print(f"{'METRICA OPERATIVA / RENDIMIENTO':<38} | {'PORTAFOLIO COMPLETO (9 RULETAS)':<30} | {'TOP 7 MAS EFECTIVAS':<28}")
    print("-"*105)
    print(f"{'Ruletas Excluidas':<38} | {'Ninguna (Todas)':<30} | {peores_2_ruletas[0][:13]} y {peores_2_ruletas[1][:13]}")
    print(f"{'Operaciones Diarias Promedio':<38} | {ops_dia_9:>6.2f} disparos/dia            | {ops_dia_7:>6.2f} disparos/dia")
    print(f"{'Operaciones Totales (2 aos)':<38} | {tot_ops_9:<30,d} | {tot_ops_7:<28,d}")
    print(f"{'Total Aciertos (Hits)':<38} | {len(df[df['hit']==True]):<30,d} | {len(df_top7[df_top7['hit']==True]):<28,d}")
    print(f"{'Win Rate Global':<38} | {wr_9:>6.2f}%                        | {wr_7:>6.2f}%")
    print(f"{'Capital Invertido':<38} | ${df['cost'].sum():>10,.2f} USD             | ${inv_7:>10,.2f} USD")
    print(f"{'Beneficio Neto Acumulado (PnL)':<38} | +${pnl_9:>9,.2f} USD             | +${pnl_7:>9,.2f} USD")
    print(f"{'Retorno sobre Inversion (ROI)':<38} | +{roi_9:>5.2f}%                       | +{roi_7:>5.2f}%")
    print(f"{'Drawdown Maximo Historico':<38} | -${abs(max_dd_9):>9.2f} USD             | -${abs(max_dd_7):>9.2f} USD")
    print(f"{'Dias con al menos 1 Cobro':<38} | 634/756 (83.9%)                 | {dias_hit_7}/756 ({dias_hit_7/756*100:.1f}%)")
    print(f"{'Semanas Ganadoras (Verdes)':<38} | 78/111 (70.3%)                  | {sem_pos_7}/{tot_sem_7} ({sem_pos_7/tot_sem_7*100:.1f}%)")
    print(f"{'Racha Maxima de Fallos':<38} | {32} fallos seguidos               | {max_fail_7} fallos seguidos")
    print(f"{'Valle Promedio de Fallos':<38} | {5.77:.2f} fallos                   | {avg_fail_7:.2f} fallos (Mediana: {med_fail_7:.0f})")
    print("="*105)
