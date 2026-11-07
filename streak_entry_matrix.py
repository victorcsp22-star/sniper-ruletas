import os
import sys
import pandas as pd
import numpy as np

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DATA_DIR = r"C:\Users\victo\nuevas_ruletas"

CONFIG = {
    "Gatazo": {
        "file": os.path.join(DATA_DIR, "gatazo.csv"),
        "total_animals": 85,
        "payout": 60.0,
        "lags": [35, 22, 20],
        "emoji": "🐯"
    },
    "Mega Animal 40": {
        "file": os.path.join(DATA_DIR, "mega_animal_40.csv"),
        "total_animals": 47,
        "payout": 30.0,
        "lags": [18, 21, 37],
        "emoji": "🦏"
    },
    "Lotto Gato": {
        "file": os.path.join(DATA_DIR, "lotto_gato.csv"),
        "total_animals": 47,
        "payout": 30.0,
        "lags": [19, 38, 16],
        "emoji": "🐱"
    },
    "Monje Millonario": {
        "file": os.path.join(DATA_DIR, "monje_millonario.csv"),
        "total_animals": 77,
        "payout": 60.0,
        "lags": [24, 35, 37],
        "emoji": "🧘‍♂️"
    },
    "Loto Chaima": {
        "file": os.path.join(DATA_DIR, "loto_chaima.csv"),
        "total_animals": 57,
        "payout": 40.0,
        "lags": [35, 29, 38],
        "emoji": "🦜"
    },
    "Granja Mill. Animalitos": {
        "file": os.path.join(DATA_DIR, "granja_millonaria_animalitos.csv"),
        "total_animals": 38,
        "payout": 30.0,
        "lags": [17, 31, 23],
        "emoji": "🚜"
    },
    "Granja Mill. Granjazo": {
        "file": os.path.join(DATA_DIR, "granja_millonaria_granjazo.csv"),
        "total_animals": 68,
        "payout": 60.0,
        "lags": [26, 14, 40],
        "emoji": "🌽"
    }
}

target_streaks = [0, 1, 2, 3, 4, 5, 6, 7]

def evaluate_streak_entries(name: str, meta: dict):
    filepath = meta["file"]
    if not os.path.exists(filepath):
        return None

    df = pd.read_csv(filepath, dtype={"numero": str})
    df["numero"] = df["numero"].astype(str).str.strip()
    df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
    df = df.sort_values(by="sort_dt").reset_index(drop=True)
    nums = df["numero"].tolist()
    total_sorteos = len(nums)
    
    lags = meta["lags"]
    payout = meta["payout"]
    be_rate = (1.0 / payout) * 100.0
    max_l = max(lags)

    # Rastrear cada oportunidad con su racha previa
    records = []
    streak = 0

    for i in range(max_l + 7, total_sorteos):
        actual = nums[i]
        rec6 = set(nums[i-6:i])
        cands = list({nums[i-l] for l in lags} - rec6)
        
        if cands:
            cost = len(cands)
            hit = (actual in cands)
            
            records.append({
                "i": i,
                "streak_previa": streak,
                "cost": cost,
                "hit": hit
            })
            
            if hit:
                streak = 0
            else:
                streak += 1

    df_rec = pd.DataFrame(records)
    
    # Evaluar para cada racha de entrada
    streak_rows = []
    for s_target in target_streaks:
        sub = df_rec[df_rec["streak_previa"] == s_target]
        disparos = len(sub)
        if disparos == 0:
            streak_rows.append({
                "racha": s_target,
                "label": f"Racha {s_target} ({'Luego de Ganar' if s_target==0 else f'Luego de Perder {s_target}'})",
                "disparos": 0,
                "fichas": 0,
                "prom_fichas": 0,
                "ganadas": 0,
                "perdidas": 0,
                "win_rate": 0.0,
                "invested": 0.0,
                "collected": 0.0,
                "pnl": 0.0,
                "roi": 0.0
            })
            continue

        ganadas = int(sub["hit"].sum())
        perdidas = disparos - ganadas
        wr = (ganadas / disparos * 100.0)
        fichas = int(sub["cost"].sum())
        inv = fichas * 1.0 # $1 por animal
        cob = ganadas * payout * 1.0
        pnl = cob - inv
        roi = (pnl / inv * 100.0) if inv > 0 else 0.0

        label = "Luego de Ganar (Racha 0)" if s_target == 0 else f"Luego de Perder {s_target} (Racha {s_target})"
        streak_rows.append({
            "racha": s_target,
            "label": label,
            "disparos": disparos,
            "fichas": fichas,
            "prom_fichas": fichas / disparos,
            "ganadas": ganadas,
            "perdidas": perdidas,
            "win_rate": wr,
            "invested": inv,
            "collected": cob,
            "pnl": pnl,
            "roi": roi
        })

    return {
        "name": name,
        "emoji": meta["emoji"],
        "payout": payout,
        "be_rate": be_rate,
        "lags": lags,
        "total_sorteos": total_sorteos,
        "df_streaks": pd.DataFrame(streak_rows)
    }

def run_all():
    all_results = {}
    for name, meta in CONFIG.items():
        res = evaluate_streak_entries(name, meta)
        if res:
            all_results[name] = res

    # Imprimir tablas
    for name, res in all_results.items():
        print("=" * 110)
        print(f" {res['emoji']} {name.upper()} | Payout: {res['payout']:.0f}x | Break-Even: {res['be_rate']:.2f}% | Lags: {res['lags']} | Sorteos: {res['total_sorteos']:,}")
        print("=" * 110)
        print(f" {'Punto de Entrada':<34} | {'Sorteos':<8} | {'Animales':<9} | {'Ganadas':<8} | {'Perdidas':<9} | {'Win Rate':<10} | {'Total Inv. ($)':<14} | {'Cobrado ($)':<12} | {'PnL Neto ($)':<14} | {'ROI Neto'}")
        print("-" * 125)
        for _, row in res["df_streaks"].iterrows():
            pnl_str = f"{'+' if row['pnl']>=0 else ''}${row['pnl']:,.2f}"
            roi_str = f"{row['roi']:+.1f}%" if row['disparos'] > 0 else "N/A"
            wr_str = f"{row['win_rate']:.2f}%" if row['disparos'] > 0 else "0.00%"
            inv_str = f"${row['invested']:,.2f}"
            cob_str = f"${row['collected']:,.2f}"
            badge = "🟢" if row['pnl'] > 0 else ("🔴" if row['disparos'] > 0 else "⚪")
            print(f" {badge} {row['label']:<32} | {row['disparos']:>7} | {row['fichas']:>8} | {row['ganadas']:>7} | {row['perdidas']:>8} | {wr_str:>9} | {inv_str:>13} | {cob_str:>11} | {pnl_str:>13} | {roi_str:>8}")
        print("=" * 125 + "\n")

if __name__ == "__main__":
    run_all()
