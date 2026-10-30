import os
import sys
import numpy as np
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RULETAS_CONFIG = {
    "Lotto Activo": {
        "file": os.path.join(BASE_DIR, "lotto_activo_2anios.csv"),
        "lags": [20, 18, 14],
        "payout": 30.0,
        "k": 38,
        "emoji": "🦁",
    },
    "La Granjita": {
        "file": os.path.join(BASE_DIR, "la_granjita_2anios.csv"),
        "lags": [15, 17],
        "payout": 30.0,
        "k": 38,
        "emoji": "🐸",
    },
    "Ruleta Royal": {
        "file": os.path.join(BASE_DIR, "ruleta_royal_2anios.csv"),
        "lags": [16, 19, 31],
        "payout": 30.0,
        "k": 37,
        "emoji": "👑",
    },
    "Guacharo Activo": {
        "file": os.path.join(BASE_DIR, "guacharo_activo_2anios.csv"),
        "lags": [31, 41, 25, 42, 35],
        "payout": 60.0,
        "k": 77,
        "emoji": "🦇",
    },
    "Selva Plus": {
        "file": os.path.join(BASE_DIR, "selva_plus_2anios.csv"),
        "lags": [35, 18, 36],
        "payout": 80.0,
        "k": 100,
        "emoji": "🌿",
    }
}

def analyze_strategy_health(window_size=50):
    print("=" * 95)
    print(" 🏥 AGENTE DE SALUD CUANTITATIVO DE LA ESTRATEGIA (MONITOREO DE EDGE Y LAGS)")
    print("=" * 95)

    health_reports = {}

    for lotto_name, cfg in RULETAS_CONFIG.items():
        df = pd.read_csv(cfg["file"], encoding="utf-8-sig", dtype={"numero": str})
        df["dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        df = df.dropna(subset=["dt"]).sort_values(by="dt").reset_index(drop=True)
        
        nums = df["numero"].tolist()
        total = len(nums)
        lags = cfg["lags"]
        payout = cfg["payout"]
        be_rate = (1.0 / payout) * 100.0
        max_lag = max(lags)

        streak = 0
        all_signals = [] # Lista de (hit, cost, dt)

        for i in range(max_lag + 7, total):
            actual = nums[i]
            rec6 = set(nums[i - 6:i])
            cands = list({nums[i - l] for l in lags} - rec6)
            cost = len(cands)
            hit = (actual in cands)

            if streak == 1 and cost > 0:
                all_signals.append({
                    "hit": hit,
                    "cost": cost,
                    "dt": df.iloc[i]["dt"]
                })

            if hit:
                streak = 0
            else:
                streak += 1

        total_trials = len(all_signals)
        total_hits = sum(1 for s in all_signals if s["hit"])
        base_win_rate = (total_hits / total_trials * 100.0) if total_trials > 0 else 0.0

        # Ventana móvil reciente (últimos N disparos reales del gatillo)
        recent_window = all_signals[-window_size:] if total_trials >= window_size else all_signals
        recent_trials = len(recent_window)
        recent_hits = sum(1 for s in recent_window if s["hit"])
        recent_win_rate = (recent_hits / recent_trials * 100.0) if recent_trials > 0 else 0.0

        # Ratio de salud: porcentaje de retención del edge histórico
        health_score = (recent_win_rate / base_win_rate * 100.0) if base_win_rate > 0 else 100.0

        # Diagnóstico
        if recent_win_rate >= base_win_rate:
            status = "🟢 SALUD EXCELENTE (+EV Sólido)"
            diagnostico = "Los lags mantienen o superan su ventaja histórica. Operación normal."
        elif recent_win_rate >= be_rate:
            status = "🟡 SALUD NORMAL (+EV Moderado)"
            diagnostico = "Rendimiento ligeramente por debajo del promedio pero rentable sobre Break-Even."
        else:
            status = "🔴 ALERTA DE DEGRADACIÓN (-EV Temporal)"
            diagnostico = f"La tasa reciente ({recent_win_rate:.2f}%) cayó por debajo del Break-Even ({be_rate:.2f}%). Monitorear."

        # Cálculo de Full Kelly con Grossman-Zhou
        avg_k = np.mean([s["cost"] for s in all_signals]) if all_signals else len(lags)
        p = base_win_rate / 100.0
        q = 1.0 - p
        b = (payout / avg_k) - 1.0
        f_star = (b * p - q) / b if b > 0 else 0.0
        f_unit = f_star / avg_k if avg_k > 0 else 0.0

        health_reports[lotto_name] = {
            "emoji": cfg["emoji"],
            "total_signals": total_trials,
            "base_win_rate": base_win_rate,
            "recent_trials": recent_trials,
            "recent_hits": recent_hits,
            "recent_win_rate": recent_win_rate,
            "be_rate": be_rate,
            "health_score": health_score,
            "status": status,
            "diagnostico": diagnostico,
            "f_unit": f_unit,
            "payout": payout
        }

        print(f"\n{cfg['emoji']} {lotto_name.upper()} (Break-Even Requerido: {be_rate:.2f}%)")
        print(f"   • Historial 2 Años: {total_hits}/{total_trials} aciertos -> Win Rate Base: {base_win_rate:.2f}%")
        print(f"   • Ventana Reciente ({recent_trials} señales): {recent_hits}/{recent_trials} aciertos -> Win Rate Reciente: {recent_win_rate:.2f}%")
        print(f"   • Índice de Salud de Lags: {health_score:5.1f}%")
        print(f"   • Estado: {status}")
        print(f"   • Diagnóstico del Agente: {diagnostico}")

    return health_reports

if __name__ == "__main__":
    analyze_strategy_health()
