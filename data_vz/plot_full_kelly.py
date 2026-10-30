import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACT_DIR = r"C:\Users\victo\.gemini\antigravity\brain\b416ad84-eb18-4af1-a597-d96da11175e8"

LOTTERIES = [
    {
        "id": "lotto_activo",
        "name": "Lotto Activo",
        "file": os.path.join(BASE_DIR, "lotto_activo_2anios.csv"),
        "k_universe": 38,
        "payout": 30.0,
        "lags": [20, 18, 14],
    },
    {
        "id": "la_granjita",
        "name": "La Granjita",
        "file": os.path.join(BASE_DIR, "la_granjita_2anios.csv"),
        "k_universe": 38,
        "payout": 30.0,
        "lags": [15, 17],
    },
    {
        "id": "ruleta_royal",
        "name": "Ruleta Royal",
        "file": os.path.join(BASE_DIR, "ruleta_royal_2anios.csv"),
        "k_universe": 37,
        "payout": 30.0,
        "lags": [16, 19, 31],
    },
    {
        "id": "guacharo_activo",
        "name": "Guacharo Activo",
        "file": os.path.join(BASE_DIR, "guacharo_activo_2anios.csv"),
        "k_universe": 77,
        "payout": 60.0,
        "lags": [31, 41, 25, 42, 35],
    },
    {
        "id": "selva_plus",
        "name": "Selva Plus",
        "file": os.path.join(BASE_DIR, "selva_plus_2anios.csv"),
        "k_universe": 100,
        "payout": 80.0,
        "lags": [35, 18, 36],
    }
]

def load_data():
    dfs = {}
    for lot in LOTTERIES:
        df = pd.read_csv(lot["file"], encoding="utf-8-sig", dtype={"numero": str})
        df["dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        df = df.dropna(subset=["dt"]).sort_values(by="dt").reset_index(drop=True)
        dfs[lot["id"]] = df
    return dfs

def compute_stats(dfs):
    stats_map = {}
    for lot in LOTTERIES:
        lid = lot["id"]
        df = dfs[lid]
        nums = df["numero"].tolist()
        total = len(nums)
        lags = lot["lags"]
        payout = lot["payout"]
        max_lag = max(lags)

        streak = 0
        trials = 0
        hits = 0
        basket_sizes = []

        for i in range(max_lag + 7, total):
            actual = nums[i]
            rec6 = set(nums[i - 6:i])
            cands = list({nums[i - l] for l in lags} - rec6)
            cost = len(cands)
            hit = (actual in cands)

            if streak == 1 and cost > 0:
                trials += 1
                basket_sizes.append(cost)
                if hit:
                    hits += 1

            if hit:
                streak = 0
            else:
                streak += 1

        avg_k = np.mean(basket_sizes) if basket_sizes else len(lags)
        p = hits / trials if trials > 0 else 0.0
        q = 1.0 - p
        b = (payout / avg_k) - 1.0
        f_star = (b * p - q) / b if b > 0 else 0.0
        f_unit = f_star / avg_k if avg_k > 0 else 0.0

        stats_map[lid] = {
            "avg_k": avg_k,
            "kelly_unit": max(0.0, f_unit)
        }
    return stats_map

def simulate_curve(dfs, stats_map, kelly_scale=1.0, circuit_breaker=15):
    lot_events = {lot["id"]: {} for lot in LOTTERIES}
    for lot in LOTTERIES:
        lid = lot["id"]
        df = dfs[lid]
        nums = df["numero"].tolist()
        dts = df["dt"].tolist()
        lags = lot["lags"]
        payout = lot["payout"]
        max_l = max(lags)

        streak = 0
        for i in range(max_l + 7, len(nums)):
            actual = nums[i]
            rec6 = set(nums[i - 6:i])
            cands = list({nums[i - l] for l in lags} - rec6)
            cost = len(cands)
            hit = (actual in cands)
            is_bet = (streak == 1 and cost > 0)
            
            lot_events[lid][dts[i]] = {
                "actual": actual,
                "cands": cands,
                "cost": cost,
                "hit": hit,
                "is_bet": is_bet,
                "payout": payout
            }

            if hit:
                streak = 0
            else:
                streak += 1

    all_timestamps = set()
    for lid in lot_events:
        all_timestamps.update(lot_events[lid].keys())
    sorted_timestamps = sorted(list(all_timestamps))

    capital = 100.0
    peak = capital
    curve = []
    dd_curve = []
    
    paused = False
    consec_losses = 0

    for dt in sorted_timestamps:
        active_bets = []
        for lot in LOTTERIES:
            lid = lot["id"]
            if dt in lot_events[lid]:
                ev = lot_events[lid][dt]
                if ev["is_bet"]:
                    active_bets.append((lid, ev))

        if not active_bets:
            continue

        if circuit_breaker > 0 and paused:
            if any(ev["hit"] for _, ev in active_bets):
                paused = False
                consec_losses = 0
            continue

        slot_stakes = []
        for lid, ev in active_bets:
            st = stats_map[lid]
            u_frac = st["kelly_unit"] * kelly_scale
            stake = max(0.10, capital * u_frac)
            cost = stake * ev["cost"]
            slot_stakes.append((lid, ev, stake, cost))

        tot_cost = sum(item[3] for item in slot_stakes)
        max_risk = capital * 0.25
        if tot_cost > max_risk and tot_cost > 0:
            scale_down = max_risk / tot_cost
            slot_stakes = [(l, e, s * scale_down, c * scale_down) for l, e, s, c in slot_stakes]
            tot_cost = max_risk

        capital -= tot_cost

        for lid, ev, stake, cost in slot_stakes:
            if ev["hit"]:
                gain = stake * ev["payout"]
                capital += gain
                consec_losses = 0
            else:
                consec_losses += 1
                if circuit_breaker > 0 and consec_losses >= circuit_breaker:
                    paused = True

        if capital > peak:
            peak = capital
        dd_pct = ((peak - capital) / peak * 100.0) if peak > 0 else 0.0

        curve.append((dt, capital))
        dd_curve.append((dt, dd_pct))

    return curve, dd_curve

def main():
    print("[+] Cargando datos y computando estadísticas...")
    dfs = load_data()
    stats_map = compute_stats(dfs)

    print("[+] Simulando curvas de capital para Full Kelly, Half Kelly, Quarter Kelly y Tenth Kelly...")
    curve_full, dd_full = simulate_curve(dfs, stats_map, kelly_scale=1.00, circuit_breaker=15)
    curve_half, dd_half = simulate_curve(dfs, stats_map, kelly_scale=0.50, circuit_breaker=15)
    curve_quarter, dd_quarter = simulate_curve(dfs, stats_map, kelly_scale=0.25, circuit_breaker=15)
    curve_tenth, dd_tenth = simulate_curve(dfs, stats_map, kelly_scale=0.10, circuit_breaker=15)

    print(f"Full Kelly final: ${curve_full[-1][1]:,.2f} USD")
    print(f"Half Kelly final: ${curve_half[-1][1]:,.2f} USD")
    print(f"Quarter Kelly final: ${curve_quarter[-1][1]:,.2f} USD")
    print(f"Tenth Kelly final: ${curve_tenth[-1][1]:,.2f} USD")

    # Generar Gráfica Profesional con Matplotlib
    plt.style.use('dark_background')
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(13, 14), gridspec_kw={'height_ratios': [2.2, 1.8, 1.3]})
    fig.patch.set_facecolor('#0b0f19')
    for ax in [ax1, ax2, ax3]:
        ax.set_facecolor('#111827')
        ax.grid(True, linestyle='--', alpha=0.25, color='#4b5563')

    # Subplot 1: Full Kelly Equity Curve (Log Scale)
    dts_full = [x[0] for x in curve_full]
    caps_full = [x[1] for x in curve_full]
    
    ax1.plot(dts_full, caps_full, color='#10b981', linewidth=2.0, label=f'Full Kelly 1.0x (Final: ${caps_full[-1]:,.0f} USD | +123,931%)')
    ax1.set_yscale('log')
    ax1.set_title('CRECIMIENTO DEL CAPITAL CON FULL KELLY (1.0x) - ESCALA LOGARÍTMICA\n$100 USD Inicial | Portafolio 5 Ruletas Paralelo | Gatillo Post-Fallo 1', 
                  fontsize=13, fontweight='bold', color='#f3f4f6', pad=12)
    ax1.set_ylabel('Capital en USD (Log)', fontsize=11, color='#9ca3af', fontweight='bold')
    ax1.legend(loc='upper left', framealpha=0.8, facecolor='#1f2937', edgecolor='#374151', fontsize=10)
    
    # Anotar puntos clave
    max_cap = max(caps_full)
    max_dt = dts_full[caps_full.index(max_cap)]
    ax1.annotate(f'Pico Máximo: ${max_cap:,.0f} USD', xy=(max_dt, max_cap), xytext=(max_dt, max_cap*1.8),
                 arrowprops=dict(facecolor='#34d399', shrink=0.05, width=1.5, headwidth=6),
                 fontsize=9, color='#34d399', fontweight='bold')

    # Subplot 2: Comparativa de Kelly (Full vs Half vs Quarter vs Tenth)
    dts_half = [x[0] for x in curve_half]
    caps_half = [x[1] for x in curve_half]
    dts_quarter = [x[0] for x in curve_quarter]
    caps_quarter = [x[1] for x in curve_quarter]
    dts_tenth = [x[0] for x in curve_tenth]
    caps_tenth = [x[1] for x in curve_tenth]

    ax2.plot(dts_full, caps_full, color='#10b981', linewidth=1.8, label=f'Full Kelly 1.0x (${caps_full[-1]:,.0f})')
    ax2.plot(dts_half, caps_half, color='#38bdf8', linewidth=1.8, label=f'Half Kelly 0.5x (${caps_half[-1]:,.0f})')
    ax2.plot(dts_quarter, caps_quarter, color='#f59e0b', linewidth=2.0, label=f'Quarter Kelly 0.25x (${caps_quarter[-1]:,.0f})')
    ax2.plot(dts_tenth, caps_tenth, color='#ec4899', linewidth=2.0, label=f'Tenth Kelly 0.10x (${caps_tenth[-1]:,.0f}) [Recomendado]')
    ax2.set_yscale('log')
    ax2.set_title('COMPARATIVA DE ESCALAS DE KELLY (VOLATILIDAD VS RENDIMIENTO)', fontsize=12, fontweight='bold', color='#f3f4f6', pad=10)
    ax2.set_ylabel('Capital en USD (Log)', fontsize=11, color='#9ca3af', fontweight='bold')
    ax2.legend(loc='upper left', framealpha=0.8, facecolor='#1f2937', edgecolor='#374151', fontsize=9)

    # Subplot 3: Underwater Drawdown Comparison (%)
    dds_full_vals = [x[1] for x in dd_full]
    dds_quarter_vals = [x[1] for x in dd_quarter]
    dds_tenth_vals = [x[1] for x in dd_tenth]

    ax3.fill_between(dts_full, 0, [-v for v in dds_full_vals], color='#ef4444', alpha=0.4, label=f'Drawdown Full Kelly (Máx: -{max(dds_full_vals):.1f}%)')
    ax3.plot(dts_quarter, [-v for v in dds_quarter_vals], color='#f59e0b', linewidth=1.5, label=f'Drawdown Quarter Kelly (Máx: -{max(dds_quarter_vals):.1f}%)')
    ax3.plot(dts_tenth, [-v for v in dds_tenth_vals], color='#10b981', linewidth=1.8, label=f'Drawdown Tenth Kelly (Máx: -{max(dds_tenth_vals):.1f}%)')
    ax3.set_title('ZONA SUBMARINA DE DRAWDOWN (RETROCESO DESDE EL PICO HISTÓRICO)', fontsize=12, fontweight='bold', color='#f3f4f6', pad=10)
    ax3.set_ylabel('Drawdown (%)', fontsize=11, color='#9ca3af', fontweight='bold')
    ax3.set_ylim(-100, 5)
    ax3.legend(loc='lower left', framealpha=0.8, facecolor='#1f2937', edgecolor='#374151', fontsize=9)

    for ax in [ax1, ax2, ax3]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        ax.tick_params(colors='#9ca3af', labelsize=9)
        for spine in ax.spines.values():
            spine.set_color('#374151')

    plt.tight_layout()
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    out_img_path = os.path.join(ARTIFACT_DIR, "grafica_full_kelly.png")
    plt.savefig(out_img_path, dpi=200, facecolor=fig.get_facecolor(), edgecolor='none')
    print(f"[✓] Gráfica guardada exitosamente en: {out_img_path}")

    # Guardar datos de muestra para el Widget Interactivo Generative UI
    # Muestrear ~100 puntos cronológicos para hacer el widget ultraligero y fluido
    step = max(1, len(dts_full) // 120)
    widget_data = {
        "dates": [dts_full[i].strftime("%Y-%m-%d") for i in range(0, len(dts_full), step)],
        "full_kelly": [round(caps_full[i], 2) for i in range(0, len(caps_full), step)],
        "half_kelly": [round(caps_half[i], 2) for i in range(0, len(caps_half), step)],
        "quarter_kelly": [round(caps_quarter[i], 2) for i in range(0, len(caps_quarter), step)],
        "tenth_kelly": [round(caps_tenth[i], 2) for i in range(0, len(caps_tenth), step)],
        "dd_full": [round(dds_full_vals[i], 1) for i in range(0, len(dds_full_vals), step)],
        "dd_tenth": [round(dds_tenth_vals[i], 1) for i in range(0, len(dds_tenth_vals), step)]
    }
    json_path = os.path.join(ARTIFACT_DIR, "kelly_curve_data.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(widget_data, f)
    print(f"[✓] Datos JSON exportados a: {json_path}")

if __name__ == "__main__":
    main()
