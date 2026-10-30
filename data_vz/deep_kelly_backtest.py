import os
import sys
import numpy as np
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOTTERIES = [
    {
        "id": "lotto_activo",
        "name": "Lotto Activo",
        "file": os.path.join(BASE_DIR, "lotto_activo_2anios.csv"),
        "k_universe": 38,
        "payout": 30.0,
        "lags": [20, 18, 14],
        "emoji": "🦁"
    },
    {
        "id": "la_granjita",
        "name": "La Granjita",
        "file": os.path.join(BASE_DIR, "la_granjita_2anios.csv"),
        "k_universe": 38,
        "payout": 30.0,
        "lags": [15, 17],
        "emoji": "🐸"
    },
    {
        "id": "ruleta_royal",
        "name": "Ruleta Royal",
        "file": os.path.join(BASE_DIR, "ruleta_royal_2anios.csv"),
        "k_universe": 37,
        "payout": 30.0,
        "lags": [16, 19, 31],
        "emoji": "👑"
    },
    {
        "id": "guacharo_activo",
        "name": "Guacharo Activo",
        "file": os.path.join(BASE_DIR, "guacharo_activo_2anios.csv"),
        "k_universe": 77,
        "payout": 60.0,
        "lags": [31, 41, 25, 42, 35],
        "emoji": "🦇"
    },
    {
        "id": "selva_plus",
        "name": "Selva Plus",
        "file": os.path.join(BASE_DIR, "selva_plus_2anios.csv"),
        "k_universe": 100,
        "payout": 80.0,
        "lags": [35, 18, 36],
        "emoji": "🌿"
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

def compute_individual_stats(dfs):
    print("=" * 95)
    print(" CÁLCULO FORMAL DEL CRITERIO DE KELLY INDIVIDUAL POR RULETA")
    print("=" * 95)
    print("Fórmula de Kelly para Cesta Multinumérica:")
    print("  b = (Payout / K) - 1   [Ratio de pago neto]")
    print("  f* = (b * p - q) / b   [Fracción Kelly óptima de la banca por canasta]")
    print("  f*_unit = f* / K       [Fracción Kelly por animal individual]")
    print("-" * 95)

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
        
        # Kelly fraction: f* = (b*p - q) / b
        f_star = (b * p - q) / b if b > 0 else 0.0
        f_unit = f_star / avg_k if avg_k > 0 else 0.0
        
        # Expected Value per dollar bet
        ev_dollar = (p * payout / avg_k) - 1.0

        stats_map[lid] = {
            "trials": trials,
            "hits": hits,
            "win_rate": p * 100.0,
            "avg_k": avg_k,
            "payout": payout,
            "b_ratio": b,
            "ev_dollar": ev_dollar * 100.0,
            "kelly_full": max(0.0, f_star),
            "kelly_unit": max(0.0, f_unit)
        }

        print(f"{lot['emoji']} {lot['name']:18s} | Muestras: {trials:4d} | Aciertos: {hits:3d} | Win Rate: {p*100:5.2f}%")
        print(f"   • Promedio canasta K: {avg_k:.2f} nums | Pago: {payout:.0f}x | Ratio b: {b:5.2f}")
        print(f"   • Ventaja (EV / $): {ev_dollar*100:+5.2f}% | Kelly Full Cesta: {f_star*100:5.2f}% | Kelly Unitario: {f_unit*100:5.3f}%\n")

    return stats_map

def run_deep_parallel_backtest(dfs, stats_map, kelly_fraction_scale=0.10, circuit_breaker=15):
    """
    Simulación paralela estricta paso a paso por slot temporal (fecha, hora).
    Garantiza que sorteos que ocurren a la misma hora (ej. 10:00 AM) se evalúan
    simultáneamente contra el capital disponible ANTES de resolver los premios.
    """
    # 1. Generar señales individuales cronológicas
    lot_events = {lot["id"]: {} for lot in LOTTERIES}
    
    for lot in LOTTERIES:
        lid = lot["id"]
        df = dfs[lid]
        nums = df["numero"].tolist()
        dts = df["dt"].tolist()
        fechas = df["fecha"].tolist()
        horas = df["hora"].tolist()
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
            
            dt_key = dts[i]
            lot_events[lid][dt_key] = {
                "fecha": fechas[i],
                "hora": horas[i],
                "actual": actual,
                "cands": cands,
                "cost": cost,
                "hit": hit,
                "is_bet": is_bet,
                "payout": payout,
                "lot_name": lot["name"]
            }

            if hit:
                streak = 0
            else:
                streak += 1

    # 2. Obtener la lista unificada y ordenada de todos los timestamps únicos
    all_timestamps = set()
    for lid in lot_events:
        all_timestamps.update(lot_events[lid].keys())
    sorted_timestamps = sorted(list(all_timestamps))

    # 3. Estado de la cartera y simulación
    init_capital = 100.0
    capital = init_capital
    peak_capital = init_capital
    max_dd_val = 0.0
    max_dd_pct = 0.0

    total_time_slots = 0
    total_bets_count = 0
    total_wins_count = 0
    total_losses_count = 0

    curr_consec_losses = 0
    max_consec_losses = 0
    curr_consec_wins = 0
    max_consec_wins = 0

    paused = False
    equity_curve = [(sorted_timestamps[0], init_capital)]
    daily_returns = []
    last_day = None
    day_start_cap = init_capital

    for dt in sorted_timestamps:
        current_day = dt.date()
        if last_day is not None and current_day != last_day:
            day_ret = (capital - day_start_cap) / day_start_cap
            daily_returns.append(day_ret)
            day_start_cap = capital
        last_day = current_day

        # Verificar qué ruletas tienen señal de apuesta en este timestamp
        active_bets = []
        for lot in LOTTERIES:
            lid = lot["id"]
            if dt in lot_events[lid]:
                ev = lot_events[lid][dt]
                if ev["is_bet"]:
                    active_bets.append((lid, ev))

        if not active_bets:
            continue

        total_time_slots += 1

        # Si el circuit breaker está activo
        if circuit_breaker > 0 and paused:
            # Paper trading: revisar si alguna apuesta activa hubiera ganado
            any_virtual_hit = any(ev["hit"] for _, ev in active_bets)
            if any_virtual_hit:
                paused = False
                curr_consec_losses = 0
            continue

        # Asignación de apuestas con Criterio de Kelly Multi-Activo
        # Para evitar sobreapalancamiento en momentos donde 3 ruletas disparan a la vez (ej. 10:00 AM)
        slot_stakes = []
        for lid, ev in active_bets:
            st = stats_map[lid]
            # Escalar el Kelly unitario por el factor solicitado (Full, Half, Quarter, etc.)
            unit_fraction = st["kelly_unit"] * kelly_fraction_scale
            # Limitar fracción unitaria a un rango prudente (mínimo $0.10)
            stake_per_animal = max(0.10, capital * unit_fraction)
            total_lot_cost = stake_per_animal * ev["cost"]
            slot_stakes.append((lid, ev, stake_per_animal, total_lot_cost))

        total_slot_cost = sum(item[3] for item in slot_stakes)

        # Si la suma de apuestas de la hora excede el 25% del capital, re-escalar proporcionalmente
        max_allowed_risk = capital * 0.25
        if total_slot_cost > max_allowed_risk and total_slot_cost > 0:
            scale_down = max_allowed_risk / total_slot_cost
            slot_stakes = [(lid, ev, s * scale_down, c * scale_down) for lid, ev, s, c in slot_stakes]
            total_slot_cost = max_allowed_risk

        # Ejecutar todas las apuestas concurrentes del slot
        capital -= total_slot_cost
        slot_won = False

        for lid, ev, stake_per_animal, cost_lot in slot_stakes:
            total_bets_count += 1
            if ev["hit"]:
                total_wins_count += 1
                curr_consec_wins += 1
                if curr_consec_wins > max_consec_wins:
                    max_consec_wins = curr_consec_wins
                curr_consec_losses = 0
                
                # Pago del premio
                payout_gain = stake_per_animal * ev["payout"]
                capital += payout_gain
                slot_won = True
            else:
                total_losses_count += 1
                curr_consec_losses += 1
                if curr_consec_losses > max_consec_losses:
                    max_consec_losses = curr_consec_losses
                curr_consec_wins = 0

                if circuit_breaker > 0 and curr_consec_losses >= circuit_breaker:
                    paused = True

        # Actualizar Drawdown
        if capital > peak_capital:
            peak_capital = capital
        dd_val = peak_capital - capital
        dd_pct = (dd_val / peak_capital * 100.0) if peak_capital > 0 else 0.0
        if dd_val > max_dd_val:
            max_dd_val = dd_val
        if dd_pct > max_dd_pct:
            max_dd_pct = dd_pct

        equity_curve.append((dt, capital))

    # Métricas avanzadas
    if last_day is not None and day_start_cap > 0:
        daily_returns.append((capital - day_start_cap) / day_start_cap)
    
    daily_returns_arr = np.array(daily_returns)
    mean_ret = np.mean(daily_returns_arr) if len(daily_returns_arr) > 0 else 0.0
    std_ret = np.std(daily_returns_arr) if len(daily_returns_arr) > 0 else 1e-6
    downside_ret = daily_returns_arr[daily_returns_arr < 0]
    downside_std = np.std(downside_ret) if len(downside_ret) > 0 else 1e-6
    
    # Anualización (365 días al año ya que juegan de lunes a domingo)
    sharpe = (mean_ret / std_ret) * np.sqrt(365) if std_ret > 0 else 0.0
    sortino = (mean_ret / downside_std) * np.sqrt(365) if downside_std > 0 else 0.0
    
    # Días totales
    total_days = (sorted_timestamps[-1] - sorted_timestamps[0]).days if len(sorted_timestamps) > 1 else 1
    cagr = ((capital / init_capital) ** (365.0 / max(1, total_days)) - 1.0) * 100.0 if capital > 0 else -100.0
    calmar = cagr / max_dd_pct if max_dd_pct > 0 else 0.0
    win_rate = (total_wins_count / total_bets_count * 100.0) if total_bets_count > 0 else 0.0
    roi = ((capital - init_capital) / init_capital * 100.0)

    return {
        "scale": kelly_fraction_scale,
        "circuit_breaker": circuit_breaker,
        "init_capital": init_capital,
        "final_capital": capital,
        "net_profit": capital - init_capital,
        "roi": roi,
        "cagr": cagr,
        "total_bets": total_bets_count,
        "total_wins": total_wins_count,
        "total_losses": total_losses_count,
        "win_rate": win_rate,
        "max_dd_val": max_dd_val,
        "max_dd_pct": max_dd_pct,
        "max_consec_losses": max_consec_losses,
        "max_consec_wins": max_consec_wins,
        "sharpe": sharpe,
        "sortino": sortino,
        "calmar": calmar,
        "total_days": total_days
    }

def main():
    dfs = load_data()
    stats_map = compute_individual_stats(dfs)

    print("=" * 95)
    print(" BACKTEST MULTI-RULETA PARALELO (5 RULETAS CON INTERÉS COMPUESTO Y KELLY)")
    print("=" * 95)
    print(f"Período simulado: 2 años completos (365 días continuos de sorteos)")
    print(f"Capital Inicial: $100.00 USD | Regla: Gatillo Post-Fallo 1 + Filtro 6h")
    print("-" * 95)

    scales = [
        ("Full Kelly (1.0x)", 1.00, 15),
        ("Half Kelly (0.5x)", 0.50, 15),
        ("Quarter Kelly (0.25x)", 0.25, 15),
        ("Tenth Kelly (0.10x)", 0.10, 15),
        ("Micro Kelly (0.05x)", 0.05, 15),
        ("Quarter Kelly (SIN Breaker)", 0.25, 0),
        ("Tenth Kelly (SIN Breaker)", 0.10, 0),
    ]

    results = []
    for label, sc, cb in scales:
        res = run_deep_parallel_backtest(dfs, stats_map, kelly_fraction_scale=sc, circuit_breaker=cb)
        res["label"] = label
        results.append(res)

    # Imprimir tabla comparativa
    headers = [
        "Estrategia / Nivel Kelly",
        "Cap. Final",
        "ROI Total",
        "CAGR Anual",
        "Max DD %",
        "Racha P.",
        "Sharpe",
        "Sortino",
        "Calmar"
    ]
    print(f"{headers[0]:<28} | {headers[1]:<11} | {headers[2]:<10} | {headers[3]:<10} | {headers[4]:<9} | {headers[5]:<8} | {headers[6]:<7} | {headers[7]:<7} | {headers[8]:<6}")
    print("-" * 105)

    for r in results:
        cap_str = f"${r['final_capital']:,.2f}"
        roi_str = f"{r['roi']:+,.1f}%"
        cagr_str = f"{r['cagr']:+,.1f}%"
        dd_str = f"{r['max_dd_pct']:.1f}%"
        streak_str = f"{r['max_consec_losses']:2d}"
        sharpe_str = f"{r['sharpe']:.2f}"
        sortino_str = f"{r['sortino']:.2f}"
        calmar_str = f"{r['calmar']:.2f}"

        print(f"{r['label']:<28} | {cap_str:<11} | {roi_str:<10} | {cagr_str:<10} | {dd_str:<9} | {streak_str:<8} | {sharpe_str:<7} | {sortino_str:<7} | {calmar_str:<6}")

    print("\n" + "=" * 95)
    print(" DETALLE PORMENORIZADO DE LA CONFIGURACIÓN RECOMENDADA (TENTH KELLY / QUARTER KELLY)")
    print("=" * 95)
    best_opt = results[3] # Tenth Kelly with Breaker
    print(f"• Estrategia: {best_opt['label']}")
    print(f"• Total apuestas ejecutadas: {best_opt['total_bets']:,}")
    print(f"• Aciertos: {best_opt['total_wins']} ({best_opt['win_rate']:.2f}%)")
    print(f"• Fallos: {best_opt['total_losses']}")
    print(f"• Capital Inicial: ${best_opt['init_capital']:,.2f} USD")
    print(f"• Capital Final: ${best_opt['final_capital']:,.2f} USD")
    print(f"• Beneficio Neto: ${best_opt['net_profit']:,.2f} USD ({best_opt['roi']:+.2f}%)")
    print(f"• Drawdown Máximo: ${best_opt['max_dd_val']:,.2f} USD ({best_opt['max_dd_pct']:.2f}%)")
    print(f"• Racha Máxima de Pérdidas Consecutivas Reales: {best_opt['max_consec_losses']} (acotada por Circuit Breaker)")
    print(f"• Racha Máxima de Ganancias Consecutivas: {best_opt['max_consec_wins']}")
    print(f"• Ratio de Sharpe Anualizado: {best_opt['sharpe']:.2f}")
    print(f"• Ratio de Sortino Anualizado: {best_opt['sortino']:.2f}")
    print(f"• Ratio de Calmar: {best_opt['calmar']:.2f}")

if __name__ == "__main__":
    main()
