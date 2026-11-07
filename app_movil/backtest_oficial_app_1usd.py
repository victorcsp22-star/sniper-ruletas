import os, sys, datetime
import pandas as pd
import numpy as np

# Configuración idéntica línea a línea de server_zero_dep.py
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
        "markov": {},
        "mirror": {},
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
        "markov": {},
        "mirror": {},
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
        "blacklist": ["75"],
        "markov": {},
        "mirror": {},
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
        "blacklist": [],
        "markov": {},
        "mirror": {},
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
        "blacklist": [],
        "markov": {},
        "mirror": {},
        "payout": 30.0,
        "emoji": "👑"
    },
    "Mega Animal 40": {
        "file": os.path.join(ROOT_DIR, "mega_animal_40.csv"),
        "title": "Mega Animal 40",
        "lags": [18, 20, 43],
        "target_streaks": [1, 2, 3],
        "wr_optimos": [1, 2],
        "rec_w": 8,
        "anti_clustering": False,
        "blacklist": ["4"],
        "markov": {},
        "mirror": {},
        "payout": 30.0,
        "emoji": "🦏"
    },
    "Gatazo": {
        "file": os.path.join(ROOT_DIR, "gatazo.csv"),
        "title": "Gatazo",
        "lags": [35, 9, 20],
        "target_streaks": [1],
        "wr_optimos": [0, 1, 3],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": ["11"],
        "markov": {},
        "mirror": {},
        "payout": 60.0,
        "emoji": "🐯"
    },
    "Monje Millonario": {
        "file": os.path.join(ROOT_DIR, "monje_millonario.csv"),
        "title": "Monje Millonario",
        "lags": [24, 42, 48],
        "target_streaks": [0, 1],
        "wr_optimos": [0, 1],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": ["75"],
        "markov": {},
        "mirror": {},
        "payout": 60.0,
        "emoji": "🧘"
    },
    "Granja Millonaria - Granjazo": {
        "file": os.path.join(ROOT_DIR, "granja_millonaria_granjazo.csv"),
        "title": "Granjazo",
        "lags": [45, 26, 15],
        "target_streaks": [1, 3],
        "wr_optimos": [0, 1],
        "rec_w": 6,
        "anti_clustering": False,
        "blacklist": [],
        "markov": {},
        "mirror": {},
        "payout": 60.0,
        "emoji": "🚜"
    }
}

STAKE_UNIT = 1.0  # $1.00 USD plano por ficha

all_events = []

for r_name, cfg in RULETAS.items():
    fpath = cfg["file"]
    if not os.path.exists(fpath):
        continue
    df = pd.read_csv(fpath)
    if len(df) < 50:
        continue
        
    df['fecha_str'] = df['fecha'].astype(str)
    df['num_str'] = df['numero'].astype(str).str.strip().str.lstrip("0").replace("", "0")
    
    nums = df['num_str'].tolist()
    dates = df['fecha_str'].tolist()
    horas = df['hora'].astype(str).tolist() if 'hora' in df.columns else [""] * len(df)
    
    lags = cfg["lags"]
    rec_w = cfg["rec_w"]
    use_anti = cfg["anti_clustering"]
    blacklist = set(str(x).strip().lstrip("0") or "0" for x in cfg["blacklist"])
    target_streaks = cfg.get("target_streaks", [1])
    payout = cfg["payout"]
    
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
        
        skip_anti = bool(use_anti and prev_was_repeat)
        trigger = (streak in target_streaks) and (not skip_anti) and (len(cands_lag) > 0)
        
        if trigger:
            hit = (actual in cands_lag)
            fichas = len(cands_lag)
            costo = fichas * STAKE_UNIT
            premio = (payout * STAKE_UNIT) if hit else 0.0
            pnl = premio - costo
            
            all_events.append({
                "fecha": d,
                "hora": h,
                "ruleta": r_name,
                "streak": streak,
                "cands": cands_lag,
                "fichas": fichas,
                "costo": costo,
                "salio": actual,
                "hit": hit,
                "premio": premio,
                "pnl": pnl,
                "payout": payout
            })
            
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

# Métricas acumuladas y Drawdown
df_res['cum_pnl'] = df_res['pnl'].cumsum()
df_res['peak'] = df_res['cum_pnl'].cummax()
df_res['drawdown'] = df_res['cum_pnl'] - df_res['peak']

# Análisis de rachas de fallos seguidas (valles)
fallos_consecutivos = []
cur_f = 0
for h in df_res['hit']:
    if h:
        fallos_consecutivos.append(cur_f)
        cur_f = 0
    else:
        cur_f += 1
fallos_consecutivos.append(cur_f)

print("="*85)
print("BACKTEST OFICIAL DE 2 AÑOS: MOTOR PURIFICADO DE LA APP (APUESTA PLANA $1.00 USD)")
print("="*85)
total_ops = len(df_res)
total_hits = len(df_res[df_res['hit'] == True])
wr = (total_hits / total_ops * 100) if total_ops > 0 else 0
tot_inv = df_res['costo'].sum()
tot_cob = df_res['premio'].sum()
net_pnl = df_res['pnl'].sum()
roi = (net_pnl / tot_inv * 100) if tot_inv > 0 else 0
max_dd = df_res['drawdown'].min()

print(f"• Total Operaciones Ejecutadas:  {total_ops:,}")
print(f"• Total Aciertos (Hits):         {total_hits:,} (Win Rate: {wr:.2f}%)")
print(f"• Capital Total Invertido:       ${tot_inv:,.2f} USD ({tot_inv:,.0f} fichas)")
print(f"• Capital Total Cobrado:         ${tot_cob:,.2f} USD")
print(f"• Ganancia Neta Total (PnL):     +${net_pnl:,.2f} USD")
print(f"• Retorno sobre Inversión (ROI): +{roi:.2f}%")
print(f"• Drawdown Máximo Histórico:     -${abs(max_dd):,.2f} USD (-{abs(max_dd):,.0f} fichas)")
print(f"• Valle Promedio entre Aciertos: {np.mean(fallos_consecutivos):.1f} fallos (Mediana: {np.median(fallos_consecutivos):.1f})")
print(f"• Racha Máxima de Fallos Seguidos: {max(fallos_consecutivos)} fallos")

print("\n" + "="*85)
print(f"{'RULETA':<30} | {'OPS':<5} | {'HITS':<5} | {'WR%':<7} | {'INVERSIÓN':<10} | {'COBRADO':<10} | {'PNL NETO':<11} | {'ROI%':<7}")
print("-"*85)
for r_name, grp in df_res.groupby('ruleta'):
    ops = len(grp)
    hits = len(grp[grp['hit'] == True])
    r_wr = (hits / ops * 100) if ops > 0 else 0
    inv = grp['costo'].sum()
    cob = grp['premio'].sum()
    p = grp['pnl'].sum()
    r_roi = (p / inv * 100) if inv > 0 else 0
    print(f"{r_name:<30} | {ops:<5} | {hits:<5} | {r_wr:5.2f}% | ${inv:<9,.0f} | ${cob:<9,.0f} | {p:+10,.1f} $ | {r_roi:+6.1f}%")

print("\n" + "="*85)
print("DESGLOSE ANUAL Y ÚLTIMO TRIMESTRE:")
print("="*85)
df_res['anio'] = df_res['fecha'].str.slice(0, 4)
for anio, grp in df_res.groupby('anio'):
    ops = len(grp)
    hits = len(grp[grp['hit'] == True])
    inv = grp['costo'].sum()
    cob = grp['premio'].sum()
    p = grp['pnl'].sum()
    a_roi = (p / inv * 100) if inv > 0 else 0
    print(f"Año {anio} | Ops: {ops:4d} | Hits: {hits:3d} | WR: {hits/ops*100:5.2f}% | Inv: ${inv:7,.0f} | Cob: ${cob:7,.0f} | PnL: {p:+8,.1f} $ | ROI: {a_roi:+6.1f}%")

# Últimos 3 meses (Ago - Nov 2026)
u3m = df_res[df_res['fecha'] >= '2026-08-01']
u_ops = len(u3m)
u_hits = len(u3m[u3m['hit'] == True])
u_inv = u3m['costo'].sum()
u_cob = u3m['premio'].sum()
u_pnl = u3m['pnl'].sum()
print(f"\nÚltimos 3 Meses (Ago-Nov 2026): {u_ops} ops | {u_hits} hits ({u_hits/u_ops*100:.2f}%) | Inv: ${u_inv:,.0f} | PnL: {u_pnl:+,.1f} $ | ROI: {u_pnl/u_inv*100:+.1f}%")
