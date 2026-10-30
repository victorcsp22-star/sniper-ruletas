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

def compute_kelly_base(dfs):
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
        be_rate = (1.0 / payout) * 100.0

        kelly_map[lid] = {
            "f_unit": f_unit,
            "base_p": p * 100.0,
            "be_rate": be_rate,
            "payout": payout
        }
    return kelly_map

def run_health_weighted_simulation(dfs, kelly_map, init_capital=1000.0, mdd_floor=0.40, use_health_weighting=True):
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
        all_signals_history = [] # historial acumulado hasta cada momento
        for i in range(max_l + 7, len(nums)):
            actual = nums[i]
            rec6 = set(nums[i - 6:i])
            cands = list({nums[i - l] for l in lags} - rec6)
            cost = len(cands)
            hit = (actual in cands)
            is_bet = (streak == 1 and cost > 0)
            
            # Copiar estado de salud previo a este sorteo
            if is_bet:
                rec_hits = sum(all_signals_history[-50:]) if len(all_signals_history) >= 10 else 0
                rec_trials = min(len(all_signals_history), 50)
                rec_wr = (rec_hits / rec_trials * 100.0) if rec_trials > 0 else kelly_map[lid]["base_p"]
            else:
                rec_wr = kelly_map[lid]["base_p"]

            lot_events[lid][dts[i]] = {
                "actual": actual,
                "cands": cands,
                "cost": cost,
                "hit": hit,
                "is_bet": is_bet,
                "payout": payout,
                "rec_wr": rec_wr
            }

            if is_bet:
                all_signals_history.append(hit)

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

        if paused:
            if any(ev["hit"] for _, ev in active_bets):
                paused = False
                consec_losses = 0
            continue

        if capital > peak:
            peak = capital
        current_dd = (peak - capital) / peak if peak > 0 else 0.0

        # Grossman-Zhou Colchón
        floor = (1.0 - mdd_floor) * peak
        cushion = max(0.0, capital - floor)
        gz_multiplier = min(1.0, max(0.0, cushion / (mdd_floor * peak))) if (mdd_floor * peak) > 0 else 1.0

        if gz_multiplier <= 0.01:
            continue

        slot_stakes = []
        for lid, ev in active_bets:
            km = kelly_map[lid]
            base_f = km["f_unit"]
            base_p = km["base_p"]
            be_rate = km["be_rate"]
            rec_wr = ev["rec_wr"]

            if use_health_weighting:
                # DISTRIBUCIÓN SEGÚN DEGRADACIÓN:
                # Si rec_wr < be_rate (degradado por debajo de break-even):
                # Reducir drásticamente la apuesta a una fracción defensiva (30% de Kelly)
                if rec_wr < be_rate:
                    health_weight = max(0.20, (rec_wr / be_rate) * 0.40)
                else:
                    # En zona rentable: modular entre 0.70x y 1.25x según la salud
                    health_weight = min(1.25, max(0.70, rec_wr / base_p))
            else:
                health_weight = 1.0

            stake = max(0.10, capital * base_f * gz_multiplier * health_weight)
            cost = stake * ev["cost"]
            slot_stakes.append((lid, ev, stake, cost, health_weight))

        tot_cost = sum(x[3] for x in slot_stakes)
        max_risk = capital * 0.25
        if tot_cost > max_risk and tot_cost > 0:
            scale_down = max_risk / tot_cost
            slot_stakes = [(l, e, s * scale_down, c * scale_down, hw) for l, e, s, c, hw in slot_stakes]
            tot_cost = max_risk

        capital -= tot_cost

        for lid, ev, stake, cost, hw in slot_stakes:
            total_bets += 1
            if ev["hit"]:
                total_wins += 1
                capital += (stake * ev["payout"])
                consec_losses = 0
            else:
                consec_losses += 1
                if consec_losses >= 15:
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
        "peak_capital": peak,
        "net_profit": capital - init_capital,
        "roi": ((capital - init_capital) / init_capital * 100.0),
        "max_dd_pct": max_dd_pct,
        "max_dd_val": max_dd_val,
        "total_bets": total_bets,
        "total_wins": total_wins,
        "win_rate": (total_wins / total_bets * 100.0) if total_bets > 0 else 0.0
    }

def main():
    dfs = load_data()
    km = compute_kelly_base(dfs)

    print("=" * 115)
    print(" COMPARATIVA: ASIGNACIÓN FIJA VS DISTRIBUCIÓN DINÁMICA POR DEGRADACIÓN DEL EDGE")
    print(" Capital Inicial: $1,000 USD | 5 Ruletas Paralelo | Cojín Grossman-Zhou MDD Floor: 40%")
    print("=" * 115)

    res_fixed = run_health_weighted_simulation(dfs, km, init_capital=1000.0, mdd_floor=0.40, use_health_weighting=False)
    res_weighted = run_health_weighted_simulation(dfs, km, init_capital=1000.0, mdd_floor=0.40, use_health_weighting=True)

    print(f"\n1. SIN DISTRIBUCIÓN POR DEGRADACIÓN (Full Kelly + GZ Fijo):")
    print(f"   • Capital Final: ${res_fixed['final_capital']:,.2f} USD")
    print(f"   • Pico ATH:      ${res_fixed['peak_capital']:,.2f} USD")
    print(f"   • Beneficio:     ${res_fixed['net_profit']:,.2f} USD ({res_fixed['roi']:+,.1f}%)")
    print(f"   • Max Drawdown:  {res_fixed['max_dd_pct']:.2f}% (-${res_fixed['max_dd_val']:,.2f} USD)")
    print(f"   • Win Rate:      {res_fixed['win_rate']:.2f}% ({res_fixed['total_wins']}/{res_fixed['total_bets']})")

    print(f"\n2. CON DISTRIBUCIÓN DINÁMICA POR DEGRADACIÓN (Agente de Salud Ponderando Capital):")
    print(f"   • Capital Final: ${res_weighted['final_capital']:,.2f} USD")
    print(f"   • Pico ATH:      ${res_weighted['peak_capital']:,.2f} USD")
    print(f"   • Beneficio:     ${res_weighted['net_profit']:,.2f} USD ({res_weighted['roi']:+,.1f}%)")
    print(f"   • Max Drawdown:  {res_weighted['max_dd_pct']:.2f}% (-${res_weighted['max_dd_val']:,.2f} USD)")
    print(f"   • Win Rate:      {res_weighted['win_rate']:.2f}% ({res_weighted['total_wins']}/{res_weighted['total_bets']})")

    diff_cap = res_weighted['final_capital'] - res_fixed['final_capital']
    diff_dd = res_fixed['max_dd_pct'] - res_weighted['max_dd_pct']
    print("\n" + "=" * 115)
    print(f" IMPACTO DE LA PONDERACIÓN POR SALUD:")
    print(f" -> Diferencia de Capital: {diff_cap:+,.2f} USD")
    print(f" -> Reducción de Drawdown: {diff_dd:+.2f}% puntos porcentuales menos de retroceso")
    print("=" * 115)

if __name__ == "__main__":
    main()
