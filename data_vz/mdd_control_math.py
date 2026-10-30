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

def run_simulation(dfs, kelly_map, method="unconstrained", alpha=0.30, gamma=2.0, circuit_breaker=15):
    # Generar eventos
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

    init_capital = 100.0
    capital = init_capital
    peak = capital
    max_dd_val = 0.0
    max_dd_pct = 0.0
    paused = False
    consec_losses = 0

    total_bets = 0
    total_wins = 0

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

        # Circuit breaker
        if circuit_breaker > 0 and paused:
            if any(ev["hit"] for _, ev in active_bets):
                paused = False
                consec_losses = 0
            continue

        # Actualizar peak
        if capital > peak:
            peak = capital
        current_dd = (peak - capital) / peak if peak > 0 else 0.0

        # DETERMINAR CAPITAL ARRIESGABLE SEGÚN EL MÉTODO MATEMÁTICO
        if method == "unconstrained":
            # Full Kelly clásico sobre 100% de la riqueza
            effective_capital = capital
        elif method == "cushion_grossman_zhou":
            # Modelo Grossman-Zhou (1993): Wealth Floor = (1 - alpha) * Peak
            # Cushion C_t = W_t - Floor_t
            floor = (1.0 - alpha) * peak
            cushion = max(0.0, capital - floor)
            # El capital base de cálculo es proporcional al colchón
            # Si el colchón se reduce, la apuesta se estrangula asintóticamente a 0
            effective_capital = cushion / alpha if alpha > 0 else 0.0
        elif method == "drawdown_damping":
            # Factor de amortiguación no lineal: f_t = f* * max(0, 1 - DD / alpha)^gamma
            damping = max(0.0, 1.0 - (current_dd / alpha)) ** gamma
            effective_capital = capital * damping
        elif method == "fractional_kelly":
            # Escala fija óptima de Thorp
            effective_capital = capital * alpha # alpha es el factor fraccional ej 0.25
        else:
            effective_capital = capital

        if effective_capital < 1.0:
            # Si el colchón está exhausto, no apostar para proteger la barrera
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
            total_bets += 1
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

    return {
        "final_capital": capital,
        "max_dd_pct": max_dd_pct,
        "max_dd_val": max_dd_val,
        "total_bets": total_bets,
        "total_wins": total_wins,
        "win_rate": (total_wins / total_bets * 100.0) if total_bets > 0 else 0.0,
        "roi": ((capital - init_capital) / init_capital * 100.0)
    }

def main():
    dfs = load_data()
    kelly_map = compute_kelly_units(dfs)

    print("=" * 100)
    print(" ANÁLISIS MATEMÁTICO: CONTROL RIGUROSO DEL MÁXIMO DRAWDOWN (MDD) EN FULL KELLY")
    print("=" * 100)

    models = [
        ("Full Kelly Clásico (Sin Control)", "unconstrained", 0.0, 1.0),
        ("Cojín de Grossman-Zhou (Techo MDD = 30%)", "cushion_grossman_zhou", 0.30, 1.0),
        ("Cojín de Grossman-Zhou (Techo MDD = 40%)", "cushion_grossman_zhou", 0.40, 1.0),
        ("Cojín de Grossman-Zhou (Techo MDD = 50%)", "cushion_grossman_zhou", 0.50, 1.0),
        ("Amortiguación No Lineal de DD (Alpha=35%, Gamma=2)", "drawdown_damping", 0.35, 2.0),
        ("Amortiguación No Lineal de DD (Alpha=50%, Gamma=2)", "drawdown_damping", 0.50, 2.0),
        ("Solución Analítica de Thorp (Quarter Kelly 0.25x)", "fractional_kelly", 0.25, 1.0),
        ("Solución Analítica de Thorp (Tenth Kelly 0.10x)", "fractional_kelly", 0.10, 1.0)
    ]

    print(f"{'Modelo Matemático de Control':<45} | {'Cap. Final':<12} | {'ROI Total':<10} | {'Max DD Real':<11} | {'Límite Teórico'}")
    print("-" * 100)

    for name, method, a, g in models:
        res = run_simulation(dfs, kelly_map, method=method, alpha=a, gamma=g, circuit_breaker=15)
        cap_str = f"${res['final_capital']:,.2f}"
        roi_str = f"{res['roi']:+,.1f}%"
        dd_str = f"{res['max_dd_pct']:.2f}%"
        lim_str = f"MDD <= {a*100:.0f}%" if method == "cushion_grossman_zhou" else ("Sin Límite" if method == "unconstrained" else f"Gradual {a*100:.0f}%")
        print(f"{name:<45} | {cap_str:<12} | {roi_str:<10} | {dd_str:<11} | {lim_str}")

if __name__ == "__main__":
    main()
