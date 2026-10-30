import os
import sys
import numpy as np
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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

def run_sim_1000(dfs, kelly_map, init_capital=1000.0, method="unconstrained", alpha=0.30, gamma=2.0, circuit_breaker=15):
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

    capital = init_capital
    peak = capital
    max_dd_val = 0.0
    max_dd_pct = 0.0
    paused = False
    consec_losses = 0

    total_bets = 0
    total_wins = 0
    max_single_bet = 0.0

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
        elif method == "fixed_fraction":
            effective_capital = capital
        else:
            effective_capital = capital

        if effective_capital < 1.0:
            continue

        slot_stakes = []
        for lid, ev in active_bets:
            if method == "fixed_fraction":
                # alpha es el % fijo por animal (ej 0.0015 = 0.15%)
                stake = max(0.10, effective_capital * alpha)
            else:
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
            total_bets += 1
            if stake > max_single_bet:
                max_single_bet = stake

            if ev["hit"]:
                total_wins += 1
                capital += (stake * ev["payout"])
                consec_losses = 0
            else:
                consec_losses += 1
                if circuit_breaker > 0 and consec_losses >= circuit_breaker:
                    paused = True

        if capital > peak:
            peak = capital
        dd_pct = ((peak - capital) / peak * 100.0) if peak > 0 else 0.0
        if dd_pct > max_dd_pct:
            max_dd_pct = dd_pct
        dd_val = peak - capital
        if dd_val > max_dd_val:
            max_dd_val = dd_val

    total_days = (all_timestamps[-1] - all_timestamps[0]).days
    cagr = ((capital / init_capital) ** (365.0 / max(1, total_days)) - 1.0) * 100.0 if capital > 0 else -100.0

    return {
        "init_capital": init_capital,
        "final_capital": capital,
        "peak_capital": peak,
        "net_profit": capital - init_capital,
        "roi": ((capital - init_capital) / init_capital * 100.0),
        "cagr": cagr,
        "max_dd_pct": max_dd_pct,
        "max_dd_val": max_dd_val,
        "max_single_bet": max_single_bet,
        "total_bets": total_bets,
        "total_wins": total_wins,
        "win_rate": (total_wins / total_bets * 100.0) if total_bets > 0 else 0.0
    }

def main():
    dfs = load_data()
    kelly_map = compute_kelly_units(dfs)

    models = [
        ("Full Kelly Clásico (1.0x)", "unconstrained", 0.0, 1.0),
        ("Amortiguación No Lineal (Damping Alpha=50%, Gamma=2)", "drawdown_damping", 0.50, 2.0),
        ("Cojín Grossman-Zhou (Límite MDD = 40%)", "cushion_grossman_zhou", 0.40, 1.0),
        ("Quarter Kelly Analítico (0.25x)", "fractional_kelly", 0.25, 1.0),
        ("Tenth Kelly Analítico (0.10x)", "fractional_kelly", 0.10, 1.0),
        ("Fijo Institucional (0.15% por animal)", "fixed_fraction", 0.0015, 1.0)
    ]

    print("=" * 115)
    print(" SIMULACIÓN DE ALCANCE FINANCIERO: CAPITAL INICIAL $1,000 USD (PORTAFOLIO 5 RULETAS)")
    print("=" * 115)
    print(f"{'Estrategia de Gestión de Capital':<45} | {'Cap. Final ($)':<16} | {'Pico ATH ($)':<16} | {'Beneficio ($)':<14} | {'ROI Total':<10} | {'Max DD %'}")
    print("-" * 115)

    for name, method, a, g in models:
        res = run_sim_1000(dfs, kelly_map, init_capital=1000.0, method=method, alpha=a, gamma=g, circuit_breaker=15)
        print(f"{name:<45} | ${res['final_capital']:<15,.2f} | ${res['peak_capital']:<15,.2f} | ${res['net_profit']:<13,.2f} | {res['roi']:<9,.1f}% | {res['max_dd_pct']:.2f}%")

if __name__ == "__main__":
    main()
