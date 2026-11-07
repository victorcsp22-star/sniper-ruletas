import sys
sys.path.append(r'C:\Users\victo\nuevas_ruletas\app_movil')
import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict
import experimento_ampliacion as exp

preloaded_data = exp.preloaded_data

def run_simulation_lags_full(n_lags):
    all_events = []
    
    # Distribucion empirica armonica de rezagos (lags)
    # Lags base suelen tener dispersion de 7 a 5 pasos
    step_offsets = [0, 7, 12, 17, 22, 27, 32, 37, 42, 47, 52, 57, 62, 67, 72, 77, 82]
    
    for r_name, d in preloaded_data.items():
        nums = d["nums"]
        dates = d["dates"]
        horas = d["horas"]
        base_lags = list(d["lags"]) # 3 lags
        
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
            
    df_ev = pd.DataFrame(all_events).sort_values(by=["fecha", "hora"]).reset_index(drop=True)
    if df_ev.empty:
        return None
        
    ops = len(df_ev)
    hits = len(df_ev[df_ev['hit'] == True])
    wr = (hits / ops * 100)
    inv = df_ev['cost'].sum()
    cob = df_ev['premio'].sum()
    pnl = df_ev['pnl'].sum()
    roi = (pnl / inv * 100) if inv > 0 else 0
    avg_fichas = inv / ops if ops > 0 else 0
    
    # Max DD y Duracion de Drawdown
    df_ev['cum_pnl'] = df_ev['pnl'].cumsum()
    df_ev['peak'] = df_ev['cum_pnl'].cummax()
    df_ev['dd'] = df_ev['cum_pnl'] - df_ev['peak']
    max_dd = df_ev['dd'].min()
    
    # Semanas
    df_ev['fecha_dt'] = pd.to_datetime(df_ev['fecha'])
    df_ev['semana'] = df_ev['fecha_dt'].dt.to_period('W-SUN')
    semanas = []
    for s, grp in df_ev.groupby('semana'):
        semanas.append(grp['pnl'].sum())
    sem_pos = len([s for s in semanas if s > 0])
    sem_neg = len([s for s in semanas if s < 0])
    tot_sem = len(semanas)
    pct_sem_pos = (sem_pos / tot_sem * 100) if tot_sem > 0 else 0
    
    # Dias
    dias = []
    for d, grp in df_ev.groupby('fecha'):
        d_hits = len(grp[grp['hit'] == True])
        d_pnl = grp['pnl'].sum()
        dias.append({'hits': d_hits, 'pnl': d_pnl})
    tot_dias = len(dias)
    dias_hit = len([d for d in dias if d['hits'] >= 1])
    pct_dias_hit = (dias_hit / tot_dias * 100) if tot_dias > 0 else 0
    
    dias_verdes = len([d for d in dias if d['pnl'] > 0])
    pct_dias_verdes = (dias_verdes / tot_dias * 100) if tot_dias > 0 else 0
    
    # Rachas de fallos (Valles)
    streaks = []
    cur_streak = 0
    for h in df_ev['hit']:
        if not h:
            cur_streak += 1
        else:
            streaks.append(cur_streak)
            cur_streak = 0
    if cur_streak > 0: streaks.append(cur_streak)
    
    max_fail = max(streaks) if streaks else 0
    avg_fail = (sum(streaks) / len(streaks)) if streaks else 0
    med_fail = float(np.median(streaks)) if streaks else 0
    
    # Indice de Armonia y Paz Mental:
    # Paz Mental = (WinRate * %DiasCobro * %SemanasVerdes) / (MaxDD * VallePromedio)
    # Calmar el estres: Maximo WinRate, Minimo Valle, Minima Racha de Fallo, Maximo Días con cobro
    
    # Ratio Calmar: Beneficio Neto / Max Drawdown (Capacidad de recuperacion psicologica)
    recovery_ratio = abs(pnl / max_dd) if max_dd != 0 else 0
    
    return {
        "n_lags": n_lags,
        "ops": ops,
        "hits": hits,
        "wr": wr,
        "fichas_op": avg_fichas,
        "inv": inv,
        "cob": cob,
        "pnl": pnl,
        "roi": roi,
        "max_dd": max_dd,
        "recovery_ratio": recovery_ratio,
        "tot_sem": tot_sem,
        "sem_pos": sem_pos,
        "pct_sem_pos": pct_sem_pos,
        "tot_dias": tot_dias,
        "dias_hit": dias_hit,
        "pct_dias_hit": pct_dias_hit,
        "dias_verdes": dias_verdes,
        "pct_dias_verdes": pct_dias_verdes,
        "max_fail": max_fail,
        "avg_fail": avg_fail,
        "med_fail": med_fail
    }

if __name__ == '__main__':
    print("Iniciando escaneo exhaustivo de Produccion vs Armonia (Lags 3 a 15)...")
    results = []
    for n in range(3, 16):
        res = run_simulation_lags_full(n)
        results.append(res)
        
    print("\n" + "="*165)
    print("ESTUDIO MULTIDIMENSIONAL DE PRODUCCION VS ARMONIA (PAZ MENTAL): LAGS 3 A 15 ($1.00 USD PLANO / 2 ANOS)")
    print("="*165)
    header = f"{'LAGS':<5} | {'WINRATE':<8} | {'FICHAS':<7} | {'INVERSION':<11} | {'PNL NETO':<12} | {'ROI%':<7} | {'MAX DD':<8} | {'REC RATIO':<10} | {'DIAS COBRO%':<12} | {'DIAS VERDE%':<12} | {'SEM VERDE%':<11} | {'RACHA MAX':<10} | {'VALLE MED'}"
    print(header)
    print("-"*165)
    for r in results:
        row = (f"{r['n_lags']:<5} | {r['wr']:>6.2f}% | {r['fichas_op']:>6.2f}  | "
               f"${r['inv']:>9,.0f} | +${r['pnl']:>9,.1f} | {r['roi']:>+5.2f}% | "
               f"${r['max_dd']:>6,.0f} | {r['recovery_ratio']:>8.1f}x   | "
               f"{r['pct_dias_hit']:>10.1f}% | {r['pct_dias_verdes']:>10.1f}% | "
               f"{r['pct_sem_pos']:>9.1f}% | {r['max_fail']:>4} fallos | {r['med_fail']:>3.1f} fallos")
        print(row)
    print("="*165)
