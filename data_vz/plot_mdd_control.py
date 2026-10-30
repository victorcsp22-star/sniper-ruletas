import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACT_DIR = r"C:\Users\victo\.gemini\antigravity\brain\b416ad84-eb18-4af1-a597-d96da11175e8"

LOTTERIES = [
    {"id": "lotto_activo", "file": os.path.join(BASE_DIR, "lotto_activo_2anios.csv"), "payout": 30.0, "lags": [20, 18, 14]},
    {"id": "la_granjita", "file": os.path.join(BASE_DIR, "la_granjita_2anios.csv"), "payout": 30.0, "lags": [15, 17]},
    {"id": "ruleta_royal", "file": os.path.join(BASE_DIR, "ruleta_royal_2anios.csv"), "payout": 30.0, "lags": [16, 19, 31]},
    {"id": "guacharo_activo", "file": os.path.join(BASE_DIR, "guacharo_activo_2anios.csv"), "payout": 60.0, "lags": [31, 41, 25, 42, 35]},
    {"id": "selva_plus", "file": os.path.join(BASE_DIR, "selva_plus_2anios.csv"), "payout": 80.0, "lags": [35, 18, 36]}
]

def load_data():
    dfs = {}
    for lot in LOTTERIES:
        df = pd.read_csv(lot["file"], encoding="utf-8-sig", dtype={"numero": str})
        df["dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        df = df.dropna(subset=["dt"]).sort_values(by="dt").reset_index(drop=True)
        dfs[lot["id"]] = df
    return dfs

def compute_kelly_units(dfs):
    kelly_map = {}
    for lot in LOTTERIES:
        lid = lot["id"]
        df = dfs[lid]
        nums = df["numero"].tolist()
        lags = lot["lags"]
        payout = lot["payout"]
        max_l = max(lags)

        streak = 0
        trials = 0
        hits = 0
        basket_sizes = []

        for i in range(max_l + 7, len(nums)):
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
        kelly_map[lid] = f_unit
    return kelly_map

def get_curve(dfs, kelly_map, method="unconstrained", alpha=0.30, gamma=2.0, circuit_breaker=15):
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

    all_timestamps = sorted(list(set().union(*[lot_events[lid].keys() for lid in lot_events])))

    capital = 100.0
    peak = capital
    paused = False
    consec_losses = 0
    curve = []
    dd_curve = []

    for dt in all_timestamps:
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

        if capital > peak:
            peak = capital
        current_dd = (peak - capital) / peak if peak > 0 else 0.0

        if method == "unconstrained":
            effective_capital = capital
        elif method == "cushion_grossman_zhou":
            floor = (1.0 - alpha) * peak
            cushion = max(0.0, capital - floor)
            effective_capital = cushion / alpha if alpha > 0 else 0.0
        elif method == "drawdown_damping":
            damping = max(0.0, 1.0 - (current_dd / alpha)) ** gamma
            effective_capital = capital * damping
        elif method == "fractional_kelly":
            effective_capital = capital * alpha
        else:
            effective_capital = capital

        if effective_capital < 1.0:
            continue

        slot_stakes = []
        for lid, ev in active_bets:
            u_frac = kelly_map[lid]
            stake = max(0.10, effective_capital * u_frac)
            cost = stake * ev["cost"]
            slot_stakes.append((lid, ev, stake, cost))

        tot_cost = sum(x[3] for x in slot_stakes)
        max_risk = capital * 0.25
        if tot_cost > max_risk and tot_cost > 0:
            scale_down = max_risk / tot_cost
            slot_stakes = [(l, e, s * scale_down, c * scale_down) for l, e, s, c in slot_stakes]
            tot_cost = max_risk

        capital -= tot_cost

        for lid, ev, stake, cost in slot_stakes:
            if ev["hit"]:
                capital += (stake * ev["payout"])
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
    dfs = load_data()
    km = compute_kelly_units(dfs)

    c_raw, dd_raw = get_curve(dfs, km, "unconstrained")
    c_gz, dd_gz = get_curve(dfs, km, "cushion_grossman_zhou", alpha=0.40)
    c_damp, dd_damp = get_curve(dfs, km, "drawdown_damping", alpha=0.50, gamma=2.0)
    c_qtr, dd_qtr = get_curve(dfs, km, "fractional_kelly", alpha=0.25)

    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 11), gridspec_kw={'height_ratios': [2.0, 1.3]})
    fig.patch.set_facecolor('#0b0f19')
    for ax in [ax1, ax2]:
        ax.set_facecolor('#111827')
        ax.grid(True, linestyle='--', alpha=0.25, color='#4b5563')

    # Panel 1: Curvas de Capital
    dts_raw = [x[0] for x in c_raw]
    caps_raw = [x[1] for x in c_raw]
    dts_gz = [x[0] for x in c_gz]
    caps_gz = [x[1] for x in c_gz]
    dts_damp = [x[0] for x in c_damp]
    caps_damp = [x[1] for x in c_damp]
    dts_qtr = [x[0] for x in c_qtr]
    caps_qtr = [x[1] for x in c_qtr]

    ax1.plot(dts_raw, caps_raw, color='#ef4444', linewidth=1.4, alpha=0.7, label=f'Full Kelly Clásico (Sin Control) - Final: ${caps_raw[-1]:,.0f}')
    ax1.plot(dts_damp, caps_damp, color='#38bdf8', linewidth=2.0, label=f'Amortiguación No Lineal (Damping) - Final: ${caps_damp[-1]:,.0f}')
    ax1.plot(dts_gz, caps_gz, color='#10b981', linewidth=2.2, label=f'Cojín de Grossman-Zhou (Límite 40%) - Final: ${caps_gz[-1]:,.0f}')
    ax1.plot(dts_qtr, caps_qtr, color='#f59e0b', linewidth=2.0, linestyle='--', label=f'Quarter Kelly Analítico (0.25x) - Final: ${caps_qtr[-1]:,.0f}')

    ax1.set_yscale('log')
    ax1.set_title('CONTROL MATEMÁTICO DEL DRAWDOWN: MODELOS DE CONTROL ÓPTIMO DE RIESGO\nEvolución del Capital ($100 USD Inicial | 5 Ruletas en Paralelo)',
                  fontsize=13, fontweight='bold', color='#f3f4f6', pad=12)
    ax1.set_ylabel('Capital en USD (Log)', fontsize=11, color='#9ca3af', fontweight='bold')
    ax1.legend(loc='upper left', framealpha=0.85, facecolor='#1f2937', edgecolor='#374151', fontsize=10)

    # Panel 2: Curvas de Drawdown (%)
    dds_raw_v = [x[1] for x in dd_raw]
    dds_gz_v = [x[1] for x in dd_gz]
    dds_damp_v = [x[1] for x in dd_damp]
    dds_qtr_v = [x[1] for x in dd_qtr]

    ax2.plot(dts_raw, [-v for v in dds_raw_v], color='#ef4444', linewidth=1.2, alpha=0.6, label=f'Full Kelly Clásico (Máx DD: -{max(dds_raw_v):.1f}%)')
    ax2.plot(dts_damp, [-v for v in dds_damp_v], color='#38bdf8', linewidth=1.8, label=f'Amortiguación Damping (Máx DD: -{max(dds_damp_v):.1f}%)')
    ax2.plot(dts_gz, [-v for v in dds_gz_v], color='#10b981', linewidth=2.2, label=f'Barrera Grossman-Zhou (Máx DD: -{max(dds_gz_v):.1f}% | Cota: 40%)')
    ax2.plot(dts_qtr, [-v for v in dds_qtr_v], color='#f59e0b', linewidth=1.8, linestyle='--', label=f'Quarter Kelly Analítico (Máx DD: -{max(dds_qtr_v):.1f}%)')

    ax2.axhline(-40.0, color='#10b981', linestyle=':', alpha=0.7, label='Techo Teórico Garantizado (-40.0%)')
    ax2.set_title('ZONA DE RETROCESO (DRAWDOWN % DESDE EL PICO): CUMPLIMIENTO DE LA BARRERA',
                  fontsize=12, fontweight='bold', color='#f3f4f6', pad=10)
    ax2.set_ylabel('Drawdown (%)', fontsize=11, color='#9ca3af', fontweight='bold')
    ax2.set_ylim(-95, 5)
    ax2.legend(loc='lower left', framealpha=0.85, facecolor='#1f2937', edgecolor='#374151', fontsize=9)

    for ax in [ax1, ax2]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        ax.tick_params(colors='#9ca3af', labelsize=9)
        for spine in ax.spines.values():
            spine.set_color('#374151')

    plt.tight_layout()
    out_path = os.path.join(ARTIFACT_DIR, "grafica_control_mdd.png")
    plt.savefig(out_path, dpi=200, facecolor=fig.get_facecolor(), edgecolor='none')
    print(f"[✓] Gráfica de control MDD guardada en: {out_path}")

if __name__ == "__main__":
    main()
