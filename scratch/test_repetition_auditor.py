import os
import sys
import json
import math
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from collections import defaultdict

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = r"C:\Users\victo\nuevas_ruletas"
sys.path.append(ROOT_DIR)
from config import RULETAS_CONFIG

class RepetitionAndTransitionAuditor:
    """
    Agente Auditor de Repetición y Emergencia de Nuevos Patrones.
    Monitorea:
      1. Tasa de repetición contigua inmediata (Lag 1 / A -> A).
      2. Tasa de repetición intradía (clusters del mismo día).
      3. Estado de salud de los patrones secuenciales catalogados (markov_snipers).
      4. Detección temprana de nuevos patrones emergentes (A -> B con Z >= 2.5 no registrados).
    """

    @staticmethod
    def audit(r_name: str, df: pd.DataFrame, cfg: Dict, window_draws: int = 120) -> Dict:
        if df.empty or len(df) < 20:
            return {"error": "Historial insuficiente"}

        k = cfg.get("k", 38 if cfg.get("payout", 30.0) == 30.0 else 77)
        p0 = 1.0 / float(k)
        nums = df["numero"].astype(str).str.strip().tolist()
        animals = df["animal"].astype(str).str.strip().tolist()
        dates = df["fecha"].astype(str).str.strip().tolist() if "fecha" in df.columns else [""] * len(nums)
        n_total = len(nums)

        num_to_anim = {}
        for n, a in zip(nums, animals):
            num_to_anim[n] = a

        eval_w = min(window_draws, n_total)
        sub_nums = nums[-eval_w:]
        sub_dates = dates[-eval_w:]

        # 1. Repetición Inmediata Contigua (Lag 1 / A -> A)
        contig_repeats = 0
        trials_contig = eval_w - 1
        for i in range(1, eval_w):
            if sub_nums[i] == sub_nums[i - 1]:
                contig_repeats += 1

        obs_rate_contig = (contig_repeats / trials_contig) if trials_contig > 0 else 0.0
        se_contig = math.sqrt(p0 * (1.0 - p0) / max(1, trials_contig))
        z_contig = (obs_rate_contig - p0) / se_contig if se_contig > 0 else 0.0

        if z_contig >= 2.0:
            rep_status = "CLUSTER_ANOMALO"
            rep_badge = "🔥 Cluster Anómalo (Alta Repetición)"
            rep_desc = f"Repetición contigua anormal ({contig_repeats}/{trials_contig}, Z={z_contig:+.2f}). Activando compuertas defensivas."
        elif z_contig <= -1.5:
            rep_status = "SUPRIMIDA"
            rep_badge = "🛡️ Repetición Suprimida"
            rep_desc = f"Repetición contigua deprimida ({contig_repeats}/{trials_contig}, Z={z_contig:+.2f}). Periodo refractario universal activo."
        else:
            rep_status = "NORMAL"
            rep_badge = "⚖️ Repetición Normal"
            rep_desc = f"Repetición contigua estándar acorde a Poisson ({contig_repeats}/{trials_contig}, {obs_rate_contig*100:.1f}% vs {p0*100:.1f}% base)."

        # 2. Repetición Intradía Hoy
        today_date = sub_dates[-1] if sub_dates else ""
        today_nums = [n for n, d in zip(sub_nums, sub_dates) if d == today_date]
        n_today = len(today_nums)
        u_today = len(set(today_nums))
        dups_today = n_today - u_today
        dup_pct_today = (dups_today / n_today * 100.0) if n_today > 0 else 0.0

        intraday_status = "NORMAL"
        if n_today >= 4 and dup_pct_today >= 35.0:
            intraday_status = "CLUSTER_INTRADIA"

        # 3. Salud de los Patrones Secuenciales Catalogados (markov_snipers)
        active_snipers = cfg.get("markov_snipers", {})
        monitored_snipers = []
        eval_markov_w = min(180, n_total)
        markov_nums = nums[-eval_markov_w:]

        for from_n, to_n in active_snipers.items():
            from_anim = num_to_anim.get(from_n, f"#{from_n}")
            to_anim = num_to_anim.get(to_n, f"#{to_n}")

            # Buscar apariciones de from_n en la ventana reciente
            occurrences_from = 0
            hits_to = 0
            for i in range(len(markov_nums) - 1):
                if markov_nums[i] == from_n:
                    occurrences_from += 1
                    if markov_nums[i + 1] == to_n:
                        hits_to += 1

            if occurrences_from == 0:
                health = "LATENTE"
                health_badge = "💤 Latente (Sin apariciones del precursor)"
            elif hits_to >= 1:
                health = "ACTIVO"
                health_badge = f"🟢 Activo ({hits_to}/{occurrences_from} aciertos recientes)"
            else:
                health = "FATIGA"
                health_badge = f"⚠️ En Fatiga ({hits_to}/{occurrences_from} aciertos recientes)"

            monitored_snipers.append({
                "from_num": from_n,
                "from_anim": from_anim,
                "to_num": to_n,
                "to_anim": to_anim,
                "occurrences": occurrences_from,
                "hits": hits_to,
                "health": health,
                "health_badge": health_badge
            })

        # 4. Detección de Nuevos Patrones Emergentes (A -> B no registrados)
        emerging_scan_w = min(250, n_total)
        scan_sub = nums[-emerging_scan_w:]
        pair_counts = defaultdict(lambda: defaultdict(int))
        count_from = defaultdict(int)

        for i in range(len(scan_sub) - 1):
            pair_counts[scan_sub[i]][scan_sub[i + 1]] += 1
            count_from[scan_sub[i]] += 1

        new_emerging = []
        for fn, to_dict in pair_counts.items():
            n_fn = count_from[fn]
            if n_fn < 4:
                continue

            for tn, cnt in to_dict.items():
                # Ignorar si ya está catalogado o es auto-repetición contigua
                if fn in active_snipers and active_snipers[fn] == tn:
                    continue
                if fn == tn:
                    continue
                if tn in cfg.get("blacklist", []):
                    continue

                prob = cnt / n_fn
                se = math.sqrt(p0 * (1.0 - p0) / n_fn)
                z = (prob - p0) / se if se > 0 else 0.0
                ev = (prob * cfg.get("payout", 30.0)) - 1.0

                if z >= 2.80 and ev >= 0.80 and cnt >= 2:
                    new_emerging.append({
                        "from_num": fn,
                        "from_anim": num_to_anim.get(fn, f"#{fn}"),
                        "to_num": tn,
                        "to_anim": num_to_anim.get(tn, f"#{tn}"),
                        "count": cnt,
                        "total_from": n_fn,
                        "prob_pct": round(prob * 100.0, 1),
                        "lift": round(prob / p0, 2),
                        "z_score": round(z, 2),
                        "ev_pct": round(ev * 100.0, 1)
                    })

        new_emerging.sort(key=lambda x: x["z_score"], reverse=True)

        return {
            "ruleta": r_name,
            "rep_status": rep_status,
            "rep_badge": rep_badge,
            "rep_desc": rep_desc,
            "z_contig": round(z_contig, 2),
            "contig_repeats": contig_repeats,
            "contig_trials": trials_contig,
            "today_date": today_date,
            "dups_today": dups_today,
            "n_today": n_today,
            "dup_pct_today": round(dup_pct_today, 1),
            "intraday_status": intraday_status,
            "monitored_snipers": monitored_snipers,
            "new_emerging": new_emerging[:3]
        }

if __name__ == "__main__":
    print("=" * 110)
    print("🧪 AUDITORÍA DEL AGENTE DE REPETICIÓN Y TRANSICIÓN EN LAS 7 RULETAS")
    print("=" * 110)
    for r_name, cfg in RULETAS_CONFIG.items():
        if not cfg.get("active", False) or "rec_w" not in cfg:
            continue
        df = pd.read_csv(cfg["file"], dtype={"numero": str})
        res = RepetitionAndTransitionAuditor.audit(r_name, df, cfg)
        print(f"\n🎲 {r_name}:")
        print(f"   • Repetición Contigua: {res['rep_badge']} (Z = {res['z_contig']:+.2f}) -> {res['rep_desc']}")
        print(f"   • Repetición Hoy ({res['today_date']}): {res['dups_today']} duplicados en {res['n_today']} sorteos ({res['dup_pct_today']}%)")
        print(f"   • Estado de Patrones Markov Catalogados ({len(res['monitored_snipers'])}):")
        for s in res['monitored_snipers']:
            print(f"       - #{s['from_num']} {s['from_anim']} -> #{s['to_num']} {s['to_anim']}: {s['health_badge']}")
        if res['new_emerging']:
            print(f"   • 🚨 NUEVOS PATRONES SECUENCIALES EMERGENTES DETECTADOS ({len(res['new_emerging'])}):")
            for e in res['new_emerging']:
                print(f"       - ✨ #{e['from_num']} {e['from_anim']} -> #{e['to_num']} {e['to_anim']} | Prob: {e['prob_pct']}% (Lift {e['lift']}x) | Z: +{e['z_score']} | EV: +{e['ev_pct']}% ({e['count']}/{e['total_from']})")
        else:
            print("   • Nuevos Patrones Emergentes: Ninguno detectado con Z >= 2.80 en la ventana reciente.")
