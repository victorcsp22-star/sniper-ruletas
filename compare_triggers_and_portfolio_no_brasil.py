"""
========================================================================================
 ANÁLISIS DE LA CARTERA SIN BRASIL (8 RULETAS) Y COMPARACIÓN DE GATILLOS
========================================================================================
Evalúa:
 1. Cartera consolidada de 8 Ruletas (Venezuela 5 + Nuevas 3), excluyendo Brasil.
 2. Comparación entre:
    A) Gatillo Uniforme: Racha == 1 para todas.
    B) Gatillo Afinado por Ruleta: Ajustado al perfil empírico óptimo de cada una.
========================================================================================
"""

import os
import sys
import pandas as pd
import numpy as np

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

VZ_DIR = r"C:\Users\victo\.gemini\antigravity\scratch\lotto_activo_bot"
NEW_DIR = r"C:\Users\victo\nuevas_ruletas"

EIGHT_RULETAS = {
    "Lotto Activo": {
        "file": os.path.join(VZ_DIR, "lotto_activo_2anios.csv"),
        "lags": [20, 18, 14],
        "payout": 30.0,
        "emoji": "🦁",
        "optimal_triggers": [1] # Racha 1
    },
    "La Granjita": {
        "file": os.path.join(VZ_DIR, "la_granjita_2anios.csv"),
        "lags": [15, 17],
        "payout": 30.0,
        "emoji": "🐸",
        "optimal_triggers": [1] # Racha 1
    },
    "Ruleta Royal": {
        "file": os.path.join(VZ_DIR, "ruleta_royal_2anios.csv"),
        "lags": [16, 19, 31],
        "payout": 30.0,
        "emoji": "👑",
        "optimal_triggers": [1] # Racha 1
    },
    "Guacharo Activo": {
        "file": os.path.join(VZ_DIR, "guacharo_activo_2anios.csv"),
        "lags": [31, 41, 25, 42, 35],
        "payout": 60.0,
        "emoji": "🦇",
        "optimal_triggers": [1] # Racha 1
    },
    "Gatazo": {
        "file": os.path.join(NEW_DIR, "gatazo.csv"),
        "lags": [35, 22, 20],
        "payout": 60.0,
        "emoji": "🐯",
        # En Gatazo, tanto Racha 1 (+92.4%) como Racha 2 (+96.2%) son súper rentables
        "optimal_triggers": [1, 2]
    },
    "Mega Animal 40": {
        "file": os.path.join(NEW_DIR, "mega_animal_40.csv"),
        "lags": [18, 21, 37],
        "payout": 30.0,
        "emoji": "🦏",
        "optimal_triggers": [1] # Racha 1 pico limpio
    },
    "Monje Millonario": {
        "file": os.path.join(NEW_DIR, "monje_millonario.csv"),
        "lags": [24, 35, 37],
        "payout": 60.0,
        "emoji": "🧘‍♂️",
        "optimal_triggers": [1] # Racha 1
    }
}

def analyze_streaks_per_ruleta():
    """Analiza el rendimiento de cada ruleta individualmente por racha de entrada."""
    results = {}
    for r_name, cfg in EIGHT_RULETAS.items():
        df = pd.read_csv(cfg["file"], dtype={"numero": str})
        df["numero"] = df["numero"].astype(str).str.strip()
        df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        df = df.sort_values(by="sort_dt").reset_index(drop=True)

        lags = cfg["lags"]
        payout = cfg["payout"]
        nums = df["numero"].tolist()
        min_idx = max(lags) + 6

        # Analizar rachas 0 a 5
        streak_data = {s: {"disp": 0, "fichas": 0, "gan": 0, "inv": 0.0, "cob": 0.0} for s in range(6)}

        streak = 0
        for i in range(min_idx, len(nums)):
            actual = nums[i]
            rec6 = set(nums[i-6:i])
            cands = list({nums[i-l] for l in lags} - rec6)

            if cands:
                cost = len(cands)
                hit = (actual in cands)

                if streak in streak_data:
                    streak_data[streak]["disp"] += 1
                    streak_data[streak]["fichas"] += cost
                    streak_data[streak]["inv"] += cost * 1.0
                    if hit:
                        streak_data[streak]["gan"] += 1
                        streak_data[streak]["cob"] += payout * 1.0

                if hit:
                    streak = 0
                else:
                    streak += 1

        res_table = []
        for s, d in streak_data.items():
            wr = (d["gan"] / d["disp"] * 100.0) if d["disp"] > 0 else 0.0
            pnl = d["cob"] - d["inv"]
            roi = (pnl / d["inv"] * 100.0) if d["inv"] > 0 else 0.0
            res_table.append({
                "racha": s,
                "disp": d["disp"],
                "fichas": d["fichas"],
                "gan": d["gan"],
                "wr": wr,
                "inv": d["inv"],
                "cob": d["cob"],
                "pnl": pnl,
                "roi": roi
            })
        results[r_name] = pd.DataFrame(res_table)
    return results

def simulate_portfolio(mode="uniform"):
    """
    mode='uniform': Racha == 1 para todas.
    mode='tuned': Usa optimal_triggers específico para cada ruleta.
    """
    total_disp = 0
    total_fichas = 0
    total_gan = 0
    total_inv = 0.0
    total_cob = 0.0
    all_events = []
    ruleta_summaries = []

    for r_name, cfg in EIGHT_RULETAS.items():
        df = pd.read_csv(cfg["file"], dtype={"numero": str})
        df["numero"] = df["numero"].astype(str).str.strip()
        df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        df = df.sort_values(by="sort_dt").reset_index(drop=True)

        lags = cfg["lags"]
        payout = cfg["payout"]
        nums = df["numero"].tolist()
        min_idx = max(lags) + 6

        target_streaks = [1] if mode == "uniform" else cfg["optimal_triggers"]

        r_disp = 0
        r_fichas = 0
        r_gan = 0
        r_inv = 0.0
        r_cob = 0.0

        streak = 0
        for i in range(min_idx, len(nums)):
            actual = nums[i]
            rec6 = set(nums[i-6:i])
            cands = list({nums[i-l] for l in lags} - rec6)

            if cands:
                cost = len(cands)
                hit = (actual in cands)

                if streak in target_streaks:
                    r_disp += 1
                    r_fichas += cost
                    inv = cost * 1.0
                    r_inv += inv
                    if hit:
                        r_gan += 1
                        cob = payout * 1.0
                        r_cob += cob
                    else:
                        cob = 0.0

                    all_events.append({
                        "dt": df.iloc[i]["sort_dt"],
                        "ruleta": r_name,
                        "inv": inv,
                        "cob": cob,
                        "pnl": cob - inv
                    })

                if hit:
                    streak = 0
                else:
                    streak += 1

        r_pnl = r_cob - r_inv
        r_wr = (r_gan / r_disp * 100.0) if r_disp > 0 else 0.0
        r_roi = (r_pnl / r_inv * 100.0) if r_inv > 0 else 0.0

        total_disp += r_disp
        total_fichas += r_fichas
        total_gan += r_gan
        total_inv += r_inv
        total_cob += r_cob

        ruleta_summaries.append({
            "Ruleta": f"{cfg['emoji']} {r_name}",
            "Gatillo": f"Racha {target_streaks}",
            "Payout": f"{payout:.0f}x",
            "Disparos": r_disp,
            "Fichas": r_fichas,
            "Ganadas": r_gan,
            "Perdidas": r_disp - r_gan,
            "Win Rate": f"{r_wr:.2f}%",
            "Invertido": f"${r_inv:,.2f}",
            "Cobrado": f"${r_cob:,.2f}",
            "PnL": f"{'+' if r_pnl>=0 else ''}${r_pnl:,.2f}",
            "ROI": f"{r_roi:+.1f}%"
        })

    tot_pnl = total_cob - total_inv
    tot_wr = (total_gan / total_disp * 100.0) if total_disp > 0 else 0.0
    tot_roi = (tot_pnl / total_inv * 100.0) if total_inv > 0 else 0.0

    return {
        "mode": mode,
        "table": pd.DataFrame(ruleta_summaries),
        "disp": total_disp,
        "fichas": total_fichas,
        "gan": total_gan,
        "per": total_disp - total_gan,
        "wr": tot_wr,
        "inv": total_inv,
        "cob": total_cob,
        "pnl": tot_pnl,
        "roi": tot_roi,
        "events": sorted(all_events, key=lambda x: x["dt"])
    }

if __name__ == "__main__":
    print("=" * 105)
    print(" 1. CARTERA SIN BRASIL (8 RULETAS) - GATILLO UNIFORME (RACHA 1 PARA TODAS)")
    print("=" * 105)
    res_uni = simulate_portfolio(mode="uniform")
    print(res_uni["table"].to_string(index=False))
    print("-" * 105)
    print(f" TOTALES CONSOLIDADOS (GATILLO UNIFORME RACHA 1):")
    print(f"  • Sorteos con Disparo:       {res_uni['disp']:,} sorteos")
    print(f"  • Fichas / Animales ($1):    {res_uni['fichas']:,} apuestas")
    print(f"  • Ganadas / Aciertos:        {res_uni['gan']:,} ({res_uni['wr']:.2f}% Win Rate)")
    print(f"  • Perdidas / Fallos:         {res_uni['per']:,}")
    print(f"  • Total Invertido ($1 Fijo): ${res_uni['inv']:,.2f} USD")
    print(f"  • Total Cobrado:             ${res_uni['cob']:,.2f} USD")
    print(f"  • Beneficio Neto (PnL):      +${res_uni['pnl']:,.2f} USD")
    print(f"  • Retorno Neto (ROI):        +{res_uni['roi']:.2f}%")
    print("=" * 105 + "\n")

    print("=" * 105)
    print(" 2. CARTERA SIN BRASIL (8 RULETAS) - GATILLO AFINADO / OPTIMIZADO POR RULETA")
    print("    (Gatazo entra en Racha 1 y 2 por doble pico de rebote; las demás en Racha 1)")
    print("=" * 105)
    res_tune = simulate_portfolio(mode="tuned")
    print(res_tune["table"].to_string(index=False))
    print("-" * 105)
    print(f" TOTALES CONSOLIDADOS (GATILLO AFINADO POR RULETA):")
    print(f"  • Sorteos con Disparo:       {res_tune['disp']:,} sorteos")
    print(f"  • Fichas / Animales ($1):    {res_tune['fichas']:,} apuestas")
    print(f"  • Ganadas / Aciertos:        {res_tune['gan']:,} ({res_tune['wr']:.2f}% Win Rate)")
    print(f"  • Perdidas / Fallos:         {res_tune['per']:,}")
    print(f"  • Total Invertido ($1 Fijo): ${res_tune['inv']:,.2f} USD")
    print(f"  • Total Cobrado:             ${res_tune['cob']:,.2f} USD")
    print(f"  • Beneficio Neto (PnL):      +${res_tune['pnl']:,.2f} USD")
    print(f"  • Retorno Neto (ROI):        +{res_tune['roi']:.2f}%")
    print("=" * 105 + "\n")
