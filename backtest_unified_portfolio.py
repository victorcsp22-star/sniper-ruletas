"""
========================================================================================
 BACKTEST INTEGRAL DE LA CARTERA UNIFICADA (VENEZUELA + BRASIL + NUEVAS RULETAS)
========================================================================================
Auditoría cuantitativa completa evaluando la estrategia Sniper Post-Fallo 1
(con filtro de recencia de 6 horas) a través de todos los activos de la cartera:

1. Cartera Tradicional Venezuela (5 Ruletas):
   - Lotto Activo (30x | Lags: [20, 18, 14])
   - La Granjita (30x | Lags: [15, 17])
   - Ruleta Royal (30x | Lags: [16, 19, 31])
   - Guácharo Activo (60x | Lags: [31, 41, 25, 42, 35])
   - Selva Plus (80x | Lags: [35, 18, 36])

2. Cartera Brasil (2 Ruletas):
   - Lotto Brasil (37x | Lags: [12, 13, 24, 25])
   - Lotto Bicho (35x | Lags: [12, 25, 13, 26])

3. Nuevas Ruletas Confirmadas (3 Ruletas):
   - Gatazo (60x | Lags: [35, 22, 20])
   - Mega Animal 40 (30x | Lags: [18, 21, 37])
   - Monje Millonario (60x | Lags: [24, 35, 37])
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

PORTFOLIOS = {
    "🇻🇪 Cartera Venezuela (5 Ruletas)": {
        "Lotto Activo": {
            "file": os.path.join(VZ_DIR, "lotto_activo_2anios.csv"),
            "lags": [20, 18, 14],
            "payout": 30.0,
            "emoji": "🦁",
            "total_animals": 38
        },
        "La Granjita": {
            "file": os.path.join(VZ_DIR, "la_granjita_2anios.csv"),
            "lags": [15, 17],
            "payout": 30.0,
            "emoji": "🐸",
            "total_animals": 38
        },
        "Ruleta Royal": {
            "file": os.path.join(VZ_DIR, "ruleta_royal_2anios.csv"),
            "lags": [16, 19, 31],
            "payout": 30.0,
            "emoji": "👑",
            "total_animals": 38
        },
        "Guacharo Activo": {
            "file": os.path.join(VZ_DIR, "guacharo_activo_2anios.csv"),
            "lags": [31, 41, 25, 42, 35],
            "payout": 60.0,
            "emoji": "🦇",
            "total_animals": 76
        },
        "Selva Plus": {
            "file": os.path.join(VZ_DIR, "selva_plus_2anios.csv"),
            "lags": [35, 18, 36],
            "payout": 80.0,
            "emoji": "🌿",
            "total_animals": 80
        }
    },
    "🇧🇷 Cartera Brasil (2 Ruletas)": {
        "Lotto Brasil": {
            "file": os.path.join(VZ_DIR, "lottobrasil_2anios.csv"),
            "lags": [12, 13, 24, 25],
            "payout": 37.0,
            "emoji": "🇧🇷",
            "total_animals": 37
        },
        "Lotto Bicho": {
            "file": os.path.join(VZ_DIR, "lottobicho_2anios.csv"),
            "lags": [12, 25, 13, 26],
            "payout": 35.0,
            "emoji": "🐆",
            "total_animals": 35
        }
    },
    "🚀 Nuevas Ruletas Confirmadas (3 Ruletas)": {
        "Gatazo": {
            "file": os.path.join(NEW_DIR, "gatazo.csv"),
            "lags": [35, 22, 20],
            "payout": 60.0,
            "emoji": "🐯",
            "total_animals": 85
        },
        "Mega Animal 40": {
            "file": os.path.join(NEW_DIR, "mega_animal_40.csv"),
            "lags": [18, 21, 37],
            "payout": 30.0,
            "emoji": "🦏",
            "total_animals": 47
        },
        "Monje Millonario": {
            "file": os.path.join(NEW_DIR, "monje_millonario.csv"),
            "lags": [24, 35, 37],
            "payout": 60.0,
            "emoji": "🧘‍♂️",
            "total_animals": 77
        }
    }
}

def run_simulation(start_date=None):
    all_events = []
    ruleta_stats = {}

    for p_name, ruletas in PORTFOLIOS.items():
        for r_name, cfg in ruletas.items():
            if not os.path.exists(cfg["file"]):
                print(f"⚠️ Archivo no encontrado: {cfg['file']}")
                continue

            df = pd.read_csv(cfg["file"], dtype={"numero": str})
            df["numero"] = df["numero"].astype(str).str.strip()
            df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
            df = df.sort_values(by="sort_dt").reset_index(drop=True)

            lags = cfg["lags"]
            payout = cfg["payout"]
            nums = df["numero"].tolist()
            min_idx = max(lags) + 6

            streak = 0
            stats = {
                "portfolio": p_name,
                "name": r_name,
                "emoji": cfg["emoji"],
                "payout": payout,
                "total_animals": cfg["total_animals"],
                "be_rate": (1.0 / payout) * 100.0,
                "draws_analyzed": len(df),
                "disparos": 0,
                "fichas": 0,
                "ganadas": 0,
                "perdidas": 0,
                "invested": 0.0,
                "collected": 0.0,
                "pnl": 0.0,
                "events": []
            }

            for i in range(min_idx, len(nums)):
                fecha = df.iloc[i]["fecha"]
                actual = nums[i]
                rec6 = set(nums[i-6:i])
                cands = list({nums[i-l] for l in lags} - rec6)

                if start_date and fecha < start_date:
                    if cands:
                        hit = (actual in cands)
                        streak = 0 if hit else (streak + 1)
                    continue

                if cands:
                    cost = len(cands)
                    hit = (actual in cands)

                    # Gatillo Sniper: Entrar tras exactamente 1 fallo
                    if streak == 1:
                        stats["disparos"] += 1
                        stats["fichas"] += cost
                        inv = cost * 1.0 # $1 fijo por animalito
                        stats["invested"] += inv

                        if hit:
                            stats["ganadas"] += 1
                            cob = payout * 1.0
                            stats["collected"] += cob
                            pnl = cob - inv
                        else:
                            stats["perdidas"] += 1
                            cob = 0.0
                            pnl = -inv

                        event = {
                            "dt": df.iloc[i]["sort_dt"],
                            "fecha": fecha,
                            "hora": df.iloc[i]["hora"],
                            "portfolio": p_name,
                            "ruleta": f"{cfg['emoji']} {r_name}",
                            "payout": payout,
                            "cands_count": cost,
                            "hit": hit,
                            "inv": inv,
                            "cob": cob,
                            "pnl": pnl
                        }
                        stats["events"].append(event)
                        all_events.append(event)

                    if hit:
                        streak = 0
                    else:
                        streak += 1

            stats["pnl"] = stats["collected"] - stats["invested"]
            stats["win_rate"] = (stats["ganadas"] / stats["disparos"] * 100.0) if stats["disparos"] > 0 else 0.0
            stats["roi"] = (stats["pnl"] / stats["invested"] * 100.0) if stats["invested"] > 0 else 0.0
            stats["avg_fichas"] = (stats["fichas"] / stats["disparos"]) if stats["disparos"] > 0 else 0.0
            ruleta_stats[r_name] = stats

    all_events.sort(key=lambda x: x["dt"])
    return ruleta_stats, all_events

def calculate_drawdown(events):
    if not events:
        return 0.0, 0.0
    cum_pnl = 0.0
    peak = 0.0
    max_dd = 0.0
    for e in events:
        cum_pnl += e["pnl"]
        if cum_pnl > peak:
            peak = cum_pnl
        dd = peak - cum_pnl
        if dd > max_dd:
            max_dd = dd
    return max_dd

def print_report(ruleta_stats, all_events, title_header):
    print("=" * 115)
    print(f" {title_header}")
    print("=" * 115)

    # Agrupar por portafolio
    p_groups = {}
    for r_name, st in ruleta_stats.items():
        p = st["portfolio"]
        if p not in p_groups:
            p_groups[p] = []
        p_groups[p].append(st)

    grand_disparos = 0
    grand_fichas = 0
    grand_ganadas = 0
    grand_perdidas = 0
    grand_inv = 0.0
    grand_cob = 0.0

    for p_name, list_st in p_groups.items():
        print(f"\n📂 {p_name.upper()}")
        print("-" * 115)
        print(f" {'Ruleta':<22} | {'Pay':<4} | {'Disp':<6} | {'Fichas':<7} | {'Prom/S':<6} | {'Gan':<5} | {'Per':<5} | {'WR%':<7} | {'Invertido':<12} | {'Cobrado':<11} | {'PnL Neto':<13} | {'ROI%'}")
        print("-" * 115)
        
        sub_disp = sum(s["disparos"] for s in list_st)
        sub_fich = sum(s["fichas"] for s in list_st)
        sub_gan = sum(s["ganadas"] for s in list_st)
        sub_per = sum(s["perdidas"] for s in list_st)
        sub_inv = sum(s["invested"] for s in list_st)
        sub_cob = sum(s["collected"] for s in list_st)
        sub_pnl = sub_cob - sub_inv
        sub_wr = (sub_gan / sub_disp * 100.0) if sub_disp > 0 else 0.0
        sub_roi = (sub_pnl / sub_inv * 100.0) if sub_inv > 0 else 0.0
        sub_prom = (sub_fich / sub_disp) if sub_disp > 0 else 0.0

        for s in list_st:
            pnl_badge = "+" if s["pnl"] >= 0 else ""
            print(f" {s['emoji']} {s['name']:<18} | {s['payout']:>2.0f}x | {s['disparos']:>6} | {s['fichas']:>7} | {s['avg_fichas']:>6.2f} | {s['ganadas']:>5} | {s['perdidas']:>5} | {s['win_rate']:>6.2f}% | ${s['invested']:>10,.2f} | ${s['collected']:>9,.2f} | {pnl_badge}${s['pnl']:>10,.2f} | {s['roi']:>+6.1f}%")

        print("-" * 115)
        pnl_b = "+" if sub_pnl >= 0 else ""
        print(f" 🔹 SUB-TOTAL {p_name.split('(')[0].strip():<10} |  --  | {sub_disp:>6} | {sub_fich:>7} | {sub_prom:>6.2f} | {sub_gan:>5} | {sub_per:>5} | {sub_wr:>6.2f}% | ${sub_inv:>10,.2f} | ${sub_cob:>9,.2f} | {pnl_b}${sub_pnl:>10,.2f} | {sub_roi:>+6.1f}%")

        grand_disparos += sub_disp
        grand_fichas += sub_fich
        grand_ganadas += sub_gan
        grand_perdidas += sub_per
        grand_inv += sub_inv
        grand_cob += sub_cob

    grand_pnl = grand_cob - grand_inv
    grand_wr = (grand_ganadas / grand_disparos * 100.0) if grand_disparos > 0 else 0.0
    grand_roi = (grand_pnl / grand_inv * 100.0) if grand_inv > 0 else 0.0
    grand_prom = (grand_fichas / grand_disparos) if grand_disparos > 0 else 0.0
    profit_factor = (grand_cob / grand_inv) if grand_inv > 0 else 0.0
    max_dd = calculate_drawdown(all_events)

    print("\n" + "=" * 115)
    print(" 🌟 RESUMEN GLOBAL CONSOLIDADO DE TODA LA CARTERA UNIFICADA (10 RULETAS EN PARALELO)")
    print("=" * 115)
    print(f"  • Sorteos Totales con Disparo Sniper (Oportunidades Ejecutadas):  {grand_disparos:,} sorteos")
    print(f"  • Fichas / Animalitos Apostados ($1.00 USD c/u):                 {grand_fichas:,} apuestas")
    print(f"  • Promedio de Animalitos Cubiertos por Disparo:                  {grand_prom:.2f} animales")
    print(f"  • 🟢 Sorteos Ganados (Aciertos):                                  {grand_ganadas:,} aciertos ({grand_wr:.2f}% Win Rate)")
    print(f"  • 🔴 Sorteos Perdidos (Fallos):                                   {grand_perdidas:,} fallos ({100 - grand_wr:.2f}%)")
    print(f"  • Total Capital Invertido ($1.00 Fijo):                          ${grand_inv:,.2f} USD")
    print(f"  • Total Capital Cobrado / Pagos:                                 ${grand_cob:,.2f} USD")
    print(f"  • 💰 BENEFICIO NETO (PnL):                                       +${grand_pnl:,.2f} USD")
    print(f"  • 📈 RENTABILIDAD NETA (ROI):                                    +{grand_roi:.2f}%")
    print(f"  • 🛡️ Factor de Beneficio (Profit Factor):                         {profit_factor:.2f}")
    print(f"  • 📉 Máximo Drawdown Histórico Agregado ($1 Fijo):               ${max_dd:,.2f} USD")
    print("=" * 115 + "\n")

    return {
        "disparos": grand_disparos,
        "fichas": grand_fichas,
        "ganadas": grand_ganadas,
        "perdidas": grand_perdidas,
        "invertido": grand_inv,
        "cobrado": grand_cob,
        "pnl": grand_pnl,
        "roi": grand_roi,
        "profit_factor": profit_factor,
        "max_dd": max_dd
    }

if __name__ == "__main__":
    # 1. Backtest Histórico Total Disponible
    ruleta_stats_tot, events_tot = run_simulation()
    res_tot = print_report(ruleta_stats_tot, events_tot, "HISTÓRICO COMPLETO DISPONIBLE - CARTERA UNIFICADA (10 RULETAS)")

    # 2. Backtest Ventana Reciente 2026 (Cuando las nuevas ruletas están 100% activas)
    ruleta_stats_2026, events_2026 = run_simulation(start_date="2026-04-01")
    res_2026 = print_report(ruleta_stats_2026, events_2026, "VENTANA SIMULTÁNEA 2026 (ABRIL A OCTUBRE 2026) - TODAS ACTIVAS")
