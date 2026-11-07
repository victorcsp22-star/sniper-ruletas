import os, sys, datetime
import pandas as pd
import numpy as np

# Configuración idéntica a server_zero_dep.py
ROOT_DIR = r"C:\Users\victo\nuevas_ruletas"

RULETAS = {
    "Lotto Gato": {
        "file": os.path.join(ROOT_DIR, "lotto_gato.csv"),
        "title": "Lotto Gato",
        "lags": [18, 38, 14],
        "target_streaks": [1, 2],
        "wr_optimos": [1, 2],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": [],
        "markov": {"14": "0", "27": "15", "3": "7"},
        "mirror": {"0": "00", "1": "10", "2": "20", "3": "30", "4": "40"},
        "payout": 60.0,
        "emoji": "🐱"
    },
    "Loto Chaima": {
        "file": os.path.join(ROOT_DIR, "loto_chaima.csv"),
        "title": "Loto Chaima",
        "lags": [49, 41, 35],
        "target_streaks": [0, 1],
        "wr_optimos": [0, 1],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": [],
        "markov": {"48": "0", "55": "0", "12": "0"},
        "mirror": {"0": "00", "5": "50", "6": "60", "7": "70"},
        "payout": 60.0,
        "emoji": "🦜"
    },
    "Guacharo Activo": {
        "file": os.path.join(ROOT_DIR, "data_vz", "guacharo_activo_2anios.csv"),
        "title": "Guacharo",
        "lags": [31, 54, 41],
        "target_streaks": [1, 3],
        "wr_optimos": [1, 3, 6],
        "rec_w": 8,
        "anti_clustering": False,
        "blacklist": [],
        "markov": {"18": "33", "27": "11", "0": "28"},
        "mirror": {"0": "00", "1": "10", "2": "20", "3": "30", "4": "40"},
        "payout": 60.0,
        "emoji": "🦇"
    },
    "Lotto Activo": {
        "file": os.path.join(ROOT_DIR, "data_vz", "lotto_activo_2anios.csv"),
        "title": "Lotto Activo",
        "lags": [20, 18, 15],
        "target_streaks": [1, 2],
        "wr_optimos": [0, 1, 2],
        "rec_w": 6,
        "anti_clustering": True,
        "blacklist": ["00"],
        "markov": {"10": "32", "25": "12", "0": "10"},
        "mirror": {"0": "00", "1": "10", "2": "20", "3": "30"},
        "payout": 30.0,
        "emoji": "🦁"
    },
    "Ruleta Royal": {
        "file": os.path.join(ROOT_DIR, "data_vz", "ruleta_royal_2anios.csv"),
        "title": "Ruleta Royal",
        "lags": [19, 16, 31],
        "target_streaks": [1],
        "wr_optimos": [0, 1, 6],
        "rec_w": 6,
        "anti_clustering": True,
        "blacklist": ["00"],
        "markov": {"32": "24", "18": "0", "0": "36"},
        "mirror": {"0": "00", "1": "10", "2": "20", "3": "30"},
        "payout": 30.0,
        "emoji": "👑"
    },
    "Mega Animal 40": {
        "file": os.path.join(ROOT_DIR, "mega_animal_40.csv"),
        "title": "Mega Animal 40",
        "lags": [36, 17, 39],
        "target_streaks": [1, 2],
        "wr_optimos": [1, 2],
        "rec_w": 5,
        "anti_clustering": False,
        "blacklist": [],
        "markov": {"30": "0", "16": "25", "11": "34"},
        "mirror": {"0": "00", "1": "10", "2": "20", "3": "30", "4": "40"},
        "payout": 30.0,
        "emoji": "🦏"
    },
    "Gatazo": {
        "file": os.path.join(ROOT_DIR, "gatazo.csv"),
        "title": "Gatazo",
        "lags": [35, 41, 15],
        "target_streaks": [1],
        "wr_optimos": [0, 1, 3],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": [],
        "markov": {"23": "42", "72": "40", "15": "0"},
        "mirror": {"0": "00", "1": "10", "2": "20", "3": "30", "4": "40", "5": "50"},
        "payout": 60.0,
        "emoji": "🐯"
    },
    "Monje Millonario": {
        "file": os.path.join(ROOT_DIR, "monje_millonario.csv"),
        "title": "Monje Millonario",
        "lags": [45, 14, 38],
        "target_streaks": [1],
        "wr_optimos": [0, 1],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": [],
        "markov": {"49": "10", "14": "0", "30": "0"},
        "mirror": {"0": "00", "5": "50", "6": "60"},
        "payout": 60.0,
        "emoji": "🧘"
    },
    "Granja Millonaria - Granjazo": {
        "file": os.path.join(ROOT_DIR, "granja_millonaria_granjazo.csv"),
        "title": "Granjazo",
        "lags": [46, 50, 24],
        "target_streaks": [1],
        "wr_optimos": [0, 1],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": [],
        "markov": {"39": "12", "70": "0", "0": "75"},
        "mirror": {"0": "00", "5": "50", "6": "60", "7": "70"},
        "payout": 60.0,
        "emoji": "🚜"
    }
}

def run_exact_backtest():
    all_events = []
    
    for r_name, cfg in RULETAS.items():
        fpath = cfg["file"]
        if not os.path.exists(fpath):
            print(f"[-] Archivo no existe: {fpath}")
            continue
        df = pd.read_csv(fpath)
        if len(df) < 50:
            continue
        
        # Normalizar columnas
        df['fecha_str'] = df['fecha'].astype(str)
        df['num_str'] = df['numero'].astype(str).str.strip().str.lstrip("0")
        df['num_str'] = df['num_str'].replace("", "0")
        
        nums = df['num_str'].tolist()
        dates = df['fecha_str'].tolist()
        horas = df['hora'].tolist() if 'hora' in df.columns else [""] * len(df)
        
        lags = cfg["lags"]
        rec_w = cfg["rec_w"]
        use_anti = cfg["anti_clustering"]
        blacklist = set(str(x).strip().lstrip("0") for x in cfg["blacklist"])
        target_streaks = cfg.get("target_streaks", [1])
        payout = cfg["payout"]
        markov = {str(k).strip().lstrip("0") or "0": str(v).strip().lstrip("0") or "0" for k, v in cfg["markov"].items()}
        
        min_k = max(max(lags), rec_w) + 1
        streak = 0
        trigger_misses = 0
        cur_d = None
        seen_today = set()
        prev_was_repeat = False
        
        for i in range(min_k, len(nums)):
            actual = nums[i]
            d = dates[i]
            h = horas[i]
            
            if d != cur_d:
                cur_d = d
                seen_today = set()
                prev_was_repeat = False
                
            rec_set = set(nums[i - rec_w : i])
            raw_cands = [nums[i - l] for l in lags if i - l >= 0]
            cands_lag = sorted(list((set(raw_cands) - rec_set) - blacklist))
            
            last_num = nums[i - 1]
            markov_target = markov.get(last_num)
            is_markov = bool(markov_target and markov_target not in rec_set and markov_target not in blacklist)
            
            # AntiCluster
            skip_anti = bool(use_anti and prev_was_repeat)
            
            # Decisión de disparo idéntica a server_zero_dep.py
            trigger = False
            cands_play = []
            tipo = ""
            
            if is_markov:
                trigger = True
                cands_play = [markov_target]
                tipo = "Markov Sniper"
            elif (streak in target_streaks) and (not skip_anti):
                trigger = True
                cands_play = cands_lag
                tipo = "Canasta Rezagados"
                
            if trigger and cands_play:
                hit = (actual in cands_play)
                cost = len(cands_play)
                win_val = payout if hit else 0.0
                pnl = win_val - cost
                
                all_events.append({
                    "fecha": d,
                    "hora": h,
                    "ruleta": r_name,
                    "tipo": tipo,
                    "cands": cands_play,
                    "cost": cost,
                    "actual": actual,
                    "hit": hit,
                    "win": win_val,
                    "pnl": pnl,
                    "payout": payout
                })
                
            # Actualización de racha (se basa en rezagados)
            if cands_lag and not skip_anti:
                hit_l = (actual in cands_lag)
                if streak in target_streaks:
                    trigger_misses = 0 if hit_l else trigger_misses + 1
                streak = 0 if hit_l else streak + 1
            elif cands_lag and skip_anti:
                hit_l = (actual in cands_lag)
                streak = 0 if hit_l else streak + 1
                if streak in target_streaks:
                    trigger_misses += 1
                    
            is_rep = (actual in seen_today)
            seen_today.add(actual)
            prev_was_repeat = is_rep

    df_res = pd.DataFrame(all_events)
    def parse_time(h_str):
        try:
            return datetime.datetime.strptime(str(h_str).strip(), "%I:%M %p").time()
        except Exception:
            return datetime.time(0, 0)
            
    df_res['hora_t'] = df_res['hora'].apply(parse_time)
    df_res = df_res.sort_values(by=['fecha', 'hora_t']).reset_index(drop=True)
    return df_res

df_res = run_exact_backtest()

print("="*80)
print(f"BACKTEST TOTAL DE LA APP DESDE HISTORIAL COMPLETO HASTA HOY (2026-11-02)")
print("="*80)
total_ops = len(df_res)
total_hits = len(df_res[df_res['hit'] == True])
wr = (total_hits / total_ops * 100) if total_ops > 0 else 0
tot_cost = df_res['cost'].sum()
tot_win = df_res['win'].sum()
net_pnl = df_res['pnl'].sum()
roi = (net_pnl / tot_cost * 100) if tot_cost > 0 else 0

# Simulación de Drawdown
df_res['cum_pnl'] = df_res['pnl'].cumsum()
df_res['peak'] = df_res['cum_pnl'].cummax()
df_res['drawdown'] = df_res['cum_pnl'] - df_res['peak']
max_dd = df_res['drawdown'].min()

print(f"• Total Operaciones: {total_ops}")
print(f"• Total Aciertos (Hits): {total_hits} (Win Rate: {wr:.2f}%)")
print(f"• Total Fichas Invertidas: {tot_cost:,.0f} fichas (Bs {tot_cost*100:,.2f})")
print(f"• Total Cobrado: {tot_win:,.0f} fichas (Bs {tot_win*100:,.2f})")
print(f"• PnL Neto Total: {net_pnl:+,.0f} fichas (Bs {net_pnl*100:+,.2f})")
print(f"• ROI sobre Inversión: {roi:+.2f}%")
print(f"• Drawdown Máximo Histórico: {max_dd:,.0f} fichas (Bs {max_dd*100:,.2f})")

print("\n" + "="*80)
print("DESGLOSE POR RULETA (COMPORTAMIENTO INDIVIDUAL)")
print("="*80)
print(f"{'RULETA':<30} | {'OPS':<5} | {'HITS':<5} | {'WR%':<7} | {'INV':<7} | {'COB':<7} | {'PNL (U)':<8} | {'ROI%':<7}")
print("-"*80)
for r_name, grp in df_res.groupby('ruleta'):
    ops = len(grp)
    hits = len(grp[grp['hit'] == True])
    r_wr = (hits / ops * 100) if ops > 0 else 0
    inv = grp['cost'].sum()
    cob = grp['win'].sum()
    p = grp['pnl'].sum()
    r_roi = (p / inv * 100) if inv > 0 else 0
    print(f"{r_name:<30} | {ops:<5} | {hits:<5} | {r_wr:5.2f}% | {inv:<7.0f} | {cob:<7.0f} | {p:+7.0f} | {r_roi:+6.1f}%")

print("\n" + "="*80)
print("AUDITORÍA DE ESTABILIDAD: COMPARATIVA ÚLTIMOS 3 MESES VS HISTORIAL ANTERIOR")
print("="*80)
sep_date = "2026-08-01"
hist_ant = df_res[df_res['fecha'] < sep_date]
reciente = df_res[df_res['fecha'] >= sep_date]

for label, sub in [("Historial Previo (antes de Ago 2026)", hist_ant), ("Últimos 3 Meses (Ago - Nov 2026)", reciente)]:
    ops = len(sub)
    hits = len(sub[sub['hit'] == True])
    sub_wr = (hits / ops * 100) if ops > 0 else 0
    inv = sub['cost'].sum()
    cob = sub['win'].sum()
    p = sub['pnl'].sum()
    sub_roi = (p / inv * 100) if inv > 0 else 0
    print(f"\n>>> {label}:")
    print(f"  • Operaciones: {ops} | Hits: {hits} | Win Rate: {sub_wr:.2f}%")
    print(f"  • Inversión: {inv:,.0f} U | Cobrado: {cob:,.0f} U | PnL: {p:+,.0f} U | ROI: {sub_roi:+.2f}%")

# Rendimiento por Mes en 2026
print("\n" + "="*80)
print("DESGLOSE MES A MES EN 2026:")
print("="*80)
df_res['mes'] = df_res['fecha'].str.slice(0, 7)
for mes, grp in df_res[df_res['fecha'] >= '2026-01-01'].groupby('mes'):
    ops = len(grp)
    hits = len(grp[grp['hit'] == True])
    inv = grp['cost'].sum()
    cob = grp['win'].sum()
    p = grp['pnl'].sum()
    m_roi = (p / inv * 100) if inv > 0 else 0
    print(f"{mes} | Ops: {ops:3d} | Hits: {hits:2d} | WR: {hits/ops*100:5.2f}% | Inv: {inv:5.0f} U | Cob: {cob:5.0f} U | PnL: {p:+6.0f} U | ROI: {m_roi:+6.1f}%")
