import sys
sys.path.append(r'C:\Users\victo\nuevas_ruletas\app_movil')
import pandas as pd
from datetime import datetime
from collections import defaultdict
import experimento_ampliacion as exp

preloaded_data = exp.preloaded_data

def simulate_n_lags(n_lags):
    all_events = []
    
    for r_name, d in preloaded_data.items():
        nums = d['nums']
        dates = d['dates']
        horas = d['horas']
        base_lags = list(d['lags'])
        
        lags = list(base_lags)
        extra_needed = n_lags - len(base_lags)
        if extra_needed > 0:
            step = 7
            for k in range(1, extra_needed + 1):
                lags.append(base_lags[0] + k * step)
        elif extra_needed < 0:
            lags = base_lags[:n_lags]
            
        target_stk = d['target_stk']
        rec_w = d['rec_w']
        use_anti = d['use_anti']
        blacklist = d['blacklist']
        payout = d['payout']
        tot_terms = d['tot_terms']
        
        min_k = max(max(lags), rec_w) + 1
        streak = 0
        cur_d = None
        seen_today = set()
        prev_was_repeat = False
        
        for i in range(min_k, len(nums)):
            act = nums[i]
            dt = dates[i]
            
            if dt != cur_d:
                cur_d = dt
                seen_today = set()
                prev_was_repeat = False
                
            rec_set = set(nums[i - rec_w : i])
            raw_cands = [nums[i - l] for l in lags if i - l >= 0]
            cands_lag = sorted(list((set(raw_cands) - rec_set) - set(blacklist)))
            
            is_repeat = (act in seen_today)
            seen_today.add(act)
            if is_repeat:
                prev_was_repeat = True
                streak = 0
                continue
                
            if len(cands_lag) == 0:
                streak = 0
                continue
                
            hit_condition = (act in cands_lag)
            if not hit_condition:
                streak += 1
            else:
                streak = 0
                
            if streak == target_stk and not prev_was_repeat:
                cost = len(cands_lag)
                is_hit = hit_condition
                pay = payout if is_hit else 0.0
                pnl = pay - cost
                all_events.append({
                    'fecha': dt,
                    'hora': horas[i],
                    'ruleta': r_name,
                    'cands': len(cands_lag),
                    'cost': cost,
                    'act': act,
                    'hit': is_hit,
                    'pnl': pnl
                })
            prev_was_repeat = False
            
    df = pd.DataFrame(all_events).sort_values(by=['fecha', 'hora'])
    
    ops = len(df)
    hits = len(df[df['hit'] == True])
    wr = (hits / ops * 100) if ops > 0 else 0
    inv = float(df['cost'].sum())
    pnl = float(df['pnl'].sum())
    roi = (pnl / inv * 100) if inv > 0 else 0
    avg_fichas = inv / ops if ops > 0 else 0
    
    # Max DD
    df['cum_pnl'] = df['pnl'].cumsum()
    df['peak'] = df['cum_pnl'].cummax()
    df['dd'] = df['cum_pnl'] - df['peak']
    max_dd = float(df['dd'].min())
    
    # Semanas
    df['fecha_dt'] = pd.to_datetime(df['fecha'])
    df['semana'] = df['fecha_dt'].dt.to_period('W-SUN')
    semanas = []
    for s, grp in df.groupby('semana'):
        s_pnl = grp['pnl'].sum()
        semanas.append(s_pnl)
    sem_pos = len([s for s in semanas if s > 0])
    sem_neg = len([s for s in semanas if s < 0])
    tot_sem = len(semanas)
    pct_sem_pos = (sem_pos / tot_sem * 100) if tot_sem > 0 else 0
    
    # Dias
    dias = []
    for d, grp in df.groupby('fecha'):
        d_hits = len(grp[grp['hit'] == True])
        d_pnl = grp['pnl'].sum()
        dias.append({'hits': d_hits, 'pnl': d_pnl})
    tot_dias = len(dias)
    dias_hit = len([d for d in dias if d['hits'] >= 1])
    pct_dias_hit = (dias_hit / tot_dias * 100) if tot_dias > 0 else 0
    
    # Rachas de fallos
    streaks = []
    cur_streak = 0
    for h in df['hit']:
        if not h:
            cur_streak += 1
        else:
            streaks.append(cur_streak)
            cur_streak = 0
    max_fail_streak = max(streaks) if streaks else 0
    avg_fail_streak = sum(streaks) / len(streaks) if streaks else 0
    
    return {
        'n_lags': n_lags,
        'ops': ops,
        'hits': hits,
        'wr': wr,
        'fichas_op': avg_fichas,
        'inv': inv,
        'pnl': pnl,
        'roi': roi,
        'max_dd': max_dd,
        'sem_pos': sem_pos,
        'sem_neg': sem_neg,
        'pct_sem_pos': pct_sem_pos,
        'dias_hit': dias_hit,
        'tot_dias': tot_dias,
        'pct_dias_hit': pct_dias_hit,
        'max_fail_streak': max_fail_streak,
        'avg_fail_streak': avg_fail_streak
    }

if __name__ == '__main__':
    all_res = []
    for n in [3, 4, 5, 6, 7]:
        res = simulate_n_lags(n)
        all_res.append(res)
    
    print('='*130)
    print('ESTUDIO MULTI-LAG COMPLETO: 3, 4, 5, 6 Y 7 LAGS ($1.00 USD PLANO POR FICHA / 2 ANOS)')
    print('='*130)
    header = f"{'LAGS':<5} | {'OPS':<5} | {'HITS':<5} | {'WINRATE':<8} | {'FICHAS':<7} | {'INVERSION':<11} | {'PNL NETO':<12} | {'ROI':<8} | {'MAX DD':<9} | {'SEM VERDES':<12} | {'DIAS HIT':<12} | {'RACHA MAX FALLOS':<16}"
    print(header)
    print('-'*130)
    for r in all_res:
        row = f"{r['n_lags']:<5} | {r['ops']:<5} | {r['hits']:<5} | {r['wr']:>6.2f}% | {r['fichas_op']:>6.2f}  | ${r['inv']:>9,.0f} | +${r['pnl']:>9,.1f} | {r['roi']:>+6.2f}% | ${r['max_dd']:>7,.0f} | {r['sem_pos']:>2}/111 ({r['pct_sem_pos']:>4.1f}%) | {r['dias_hit']:>3}/750 ({r['pct_dias_hit']:>4.1f}%) | {r['max_fail_streak']:>6} fallos"
        print(row)
    print('='*130)
