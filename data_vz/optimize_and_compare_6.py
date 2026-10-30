import sys
import numpy as np
import pandas as pd
from scipy import stats

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Definición de las loterías disponibles
LOTTERIES_DEF = [
    {
        "id": "lotto_activo",
        "name": "Lotto Activo",
        "file": "lotto_activo_2anios.csv",
        "k_universe": 38,
        "payout": 30.0,
        "max_lag": 40
    },
    {
        "id": "la_granjita",
        "name": "La Granjita",
        "file": "la_granjita_2anios.csv",
        "k_universe": 38,
        "payout": 30.0,
        "max_lag": 40
    },
    {
        "id": "ruleta_royal",
        "name": "Ruleta Royal",
        "file": "ruleta_royal_2anios.csv",
        "k_universe": 37,
        "payout": 30.0,
        "max_lag": 40
    },
    {
        "id": "guacharo_activo",
        "name": "Guacharo Activo",
        "file": "guacharo_activo_2anios.csv",
        "k_universe": 77,
        "payout": 60.0,
        "max_lag": 50
    },
    {
        "id": "guacharito_millonario",
        "name": "El Guacharito Millonario",
        "file": "guacharito_millonario_2anios.csv",
        "k_universe": 100,
        "payout": 70.0,
        "max_lag": 50
    },
    {
        "id": "selva_plus",
        "name": "Selva Plus",
        "file": "selva_plus_2anios.csv",
        "k_universe": 100,
        "payout": 80.0,
        "max_lag": 40
    }
]

def load_and_clean_data(lottery):
    df = pd.read_csv(lottery["file"], encoding="utf-8-sig", dtype={"numero": str})
    df["sort_key"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
    df = df.dropna(subset=["sort_key"]).sort_values(by="sort_key").reset_index(drop=True)
    return df

def analyze_lags_for_lottery(lottery, df):
    nums = df["numero"].tolist()
    total = len(nums)
    p0 = 1.0 / lottery["k_universe"]
    be_winrate = (1.0 / lottery["payout"]) * 100.0

    lag_records = []
    for lag in range(1, lottery["max_lag"] + 1):
        valid = total - lag
        if valid <= 0:
            continue
        matches = sum(1 for i in range(lag, total) if nums[i] == nums[i - lag])
        p_hat = matches / valid
        se = np.sqrt(p0 * (1.0 - p0) / valid) if valid > 0 else 0.001
        z = (p_hat - p0) / se if se > 0 else 0.0
        p_val = 2.0 * (1.0 - stats.norm.cdf(abs(z)))

        # Filtrado: omitir números que aparecieron en los últimos 6 sorteos
        matches_filt = 0
        trials_filt = 0
        start_i = max(25, lag)
        for i in range(start_i, total):
            cand = nums[i - lag]
            rec6 = set(nums[i - 6:i])
            if cand not in rec6:
                trials_filt += 1
                if nums[i] == cand:
                    matches_filt += 1
        p_filt = (matches_filt / trials_filt * 100.0) if trials_filt > 0 else 0.0

        lag_records.append({
            "lag": lag,
            "matches": matches,
            "valid": valid,
            "pct": p_hat * 100.0,
            "pct_filt": p_filt,
            "z": z,
            "p_val": p_val
        })

    df_lags = pd.DataFrame(lag_records)
    # Ordenar por Z-score o tasa filtrada (excluyendo lags 1-6)
    rebound_lags = df_lags[df_lags["lag"] >= 7].sort_values(by="pct_filt", ascending=False).reset_index(drop=True)
    return df_lags, rebound_lags

def optimize_basket(lottery, df, rebound_lags):
    nums = df["numero"].tolist()
    total = len(nums)
    payout = lottery["payout"]
    
    # Tomamos los top 12 lags candidatos para el bucle de optimización
    top_candidates = rebound_lags["lag"].head(12).tolist()
    
    best_config = None
    best_roi = -999.0
    all_results = []

    # Probar cestas de tamaño K = 2, 3, 4, 5
    for k_size in [2, 3, 4, 5]:
        # Evaluamos selecciones ordenadas de los mejores lags
        candidate_lags = top_candidates[:k_size]
        
        start_eval = max(candidate_lags) + 7
        streak = 0
        total_bets = 0
        hits = 0
        flat_pnl = 0.0
        consec_losses = 0
        max_consec_losses = 0
        
        for i in range(start_eval, total):
            actual = nums[i]
            rec6 = set(nums[i - 6:i])
            cands = list({nums[i - l] for l in candidate_lags} - rec6)
            hit = (actual in cands)
            cost = len(cands)
            
            # Gatillo Post-Fallo 1
            if streak == 1 and cost > 0:
                total_bets += cost
                if hit:
                    hits += 1
                    flat_pnl += (payout - cost)
                    consec_losses = 0
                else:
                    flat_pnl -= cost
                    consec_losses += 1
                    if consec_losses > max_consec_losses:
                        max_consec_losses = consec_losses
                        
            if hit:
                streak = 0
            else:
                streak += 1

        roi = (flat_pnl / total_bets * 100.0) if total_bets > 0 else -100.0
        win_rate = (hits / (total_bets / len(candidate_lags)) * 100.0) if total_bets > 0 else 0.0
        
        res = {
            "k_size": k_size,
            "lags": candidate_lags,
            "total_bets": total_bets,
            "hits": hits,
            "win_rate": win_rate,
            "flat_pnl": flat_pnl,
            "roi": roi,
            "max_loss_streak": max_consec_losses
        }
        all_results.append(res)
        
        if roi > best_roi and total_bets >= 50:
            best_roi = roi
            best_config = res

    # Si ninguna cumplió umbral mínimo, tomar la primera
    if best_config is None and all_results:
        best_config = sorted(all_results, key=lambda x: x["roi"], reverse=True)[0]

    return best_config, all_results

def main():
    print("=========================================================================================")
    print(" FASE 1: BÚSQUEDA DE LAGS PREFERIDOS Y OPTIMIZACIÓN DE CESTAS PARA LAS 6 RULETAS")
    print("=========================================================================================\n")

    optimal_configs = {}
    dfs = {}

    for lot in LOTTERIES_DEF:
        df = load_and_clean_data(lot)
        dfs[lot["id"]] = df
        df_lags, rebound_lags = analyze_lags_for_lottery(lot, df)
        best_cfg, all_results = optimize_basket(lot, df, rebound_lags)
        optimal_configs[lot["id"]] = {
            "lags": best_cfg["lags"],
            "payout": lot["payout"],
            "k_universe": lot["k_universe"],
            "name": lot["name"]
        }

        be = (1.0 / lot["payout"]) * 100.0
        print(f"\n--- {lot['name'].upper()} ({lot['k_universe']} núms | Pago: {lot['payout']}x | BE: {be:.2f}%) ---")
        print(f"Total sorteos: {len(df):,}")
        print("Top 5 Lags con Mayor Rebote Filtrado (lag >= 7):")
        for idx, row in rebound_lags.head(5).iterrows():
            lag_val = int(row['lag'])
            print(f"  #{idx+1}: Lag {lag_val:2d} -> Prob Filt: {row['pct_filt']:5.2f}% | Z-Score: {row['z']:+5.2f} | Supera BE: {'SI' if row['pct_filt'] > be else 'NO'}")
            
        print(f"Configuración Óptima Seleccionada: Lags {best_cfg['lags']} (K={best_cfg['k_size']})")
        print(f"  -> ROI Individual: {best_cfg['roi']:+.2f}% | PnL Plano: {best_cfg['flat_pnl']:+.0f} uds | Aciertos: {best_cfg['hits']} | Racha Pérdidas Máx: {best_cfg['max_loss_streak']}")

    print("\n" + "=" * 95)
    print(" RESUMEN DE PARÁMETROS ÓPTIMOS POR RULETA")
    print("=" * 95)
    for lid, cfg in optimal_configs.items():
        print(f" • {cfg['name']:25s} -> Lags Preferidos: {str(cfg['lags']):16s} (Pago: {cfg['payout']}x)")

    print("\n" + "=" * 95)
    print(" FASE 2: SIMULACIÓN PARALELA MULTI-RULETA (PORTAFOLIO GLOBAL)")
    print("=========================================================================================\n")

    # Compararemos 2 portafolios:
    # Portfolio 4: Lotto Activo, La Granjita, Ruleta Royal, Guacharo Activo
    # Portfolio 6: Las 4 anteriores + El Guacharito Millonario + Selva Plus

    def run_portfolio_simulation(portfolio_ids, portfolio_name, use_circuit_breaker=True):
        # 1. Recolectar todos los sorteos de las loterías en el portafolio
        events = []
        for lid in portfolio_ids:
            df = dfs[lid]
            cfg = optimal_configs[lid]
            lags = cfg["lags"]
            max_l = max(lags)
            payout = cfg["payout"]
            nums = df["numero"].tolist()
            
            # Recorrer sorteos individuales para generar eventos cronológicos
            streak = 0
            for i in range(max_l + 7, len(nums)):
                actual = nums[i]
                rec6 = set(nums[i - 6:i])
                cands = list({nums[i - l] for l in lags} - rec6)
                cost = len(cands)
                hit = (actual in cands)
                
                # Gatillo Post-Fallo 1
                is_bet = (streak == 1 and cost > 0)
                
                events.append({
                    "timestamp": df.iloc[i]["sort_key"],
                    "lottery_id": lid,
                    "lottery_name": cfg["name"],
                    "hora": df.iloc[i]["hora"],
                    "fecha": df.iloc[i]["fecha"],
                    "actual": actual,
                    "cands": cands,
                    "cost": cost,
                    "hit": hit,
                    "is_bet": is_bet,
                    "payout": payout
                })
                
                if hit:
                    streak = 0
                else:
                    streak += 1

        # 2. Ordenar todos los eventos cronológicamente
        events.sort(key=lambda x: x["timestamp"])

        # 3. Simular en paralelo con Bankroll Unificado
        init_capital = 100.0
        capital = init_capital
        peak_capital = init_capital
        max_dd_val = 0.0
        max_dd_pct = 0.0

        total_plays = 0
        total_wins = 0
        total_losses = 0
        flat_pnl = 0.0

        curr_consec_losses = 0
        max_consec_losses = 0
        curr_consec_wins = 0
        max_consec_wins = 0

        # Circuito de seguridad
        paused = False
        consec_losses_trigger = 15

        for ev in events:
            if not ev["is_bet"]:
                continue

            hit = ev["hit"]
            cost = ev["cost"]
            payout = ev["payout"]

            # Si el circuito de seguridad está activo
            if use_circuit_breaker and paused:
                # Estamos en pausa operativa virtual (paper trading)
                if hit:
                    paused = False
                    curr_consec_losses = 0
                continue

            # Apuesta real
            total_plays += 1
            bet_per_animal = capital * 0.0015  # 0.15% del equity actual por animalito
            total_bet_cost = bet_per_animal * cost

            if hit:
                total_wins += 1
                curr_consec_wins += 1
                if curr_consec_wins > max_consec_wins:
                    max_consec_wins = curr_consec_wins
                curr_consec_losses = 0
                
                flat_pnl += (payout - cost)
                gain = (bet_per_animal * payout) - total_bet_cost
                capital += gain
            else:
                total_losses += 1
                curr_consec_losses += 1
                if curr_consec_losses > max_consec_losses:
                    max_consec_losses = curr_consec_losses
                curr_consec_wins = 0
                
                flat_pnl -= cost
                capital -= total_bet_cost

                if use_circuit_breaker and curr_consec_losses >= consec_losses_trigger:
                    paused = True

            # Track Drawdown
            if capital > peak_capital:
                peak_capital = capital
            dd_val = peak_capital - capital
            dd_pct = (dd_val / peak_capital * 100.0) if peak_capital > 0 else 0.0
            if dd_val > max_dd_val:
                max_dd_val = dd_val
            if dd_pct > max_dd_pct:
                max_dd_pct = dd_pct

        win_rate = (total_wins / total_plays * 100.0) if total_plays > 0 else 0.0
        roi = ((capital - init_capital) / init_capital * 100.0)

        return {
            "name": portfolio_name,
            "total_plays": total_plays,
            "total_wins": total_wins,
            "total_losses": total_losses,
            "win_rate": win_rate,
            "flat_pnl": flat_pnl,
            "max_consec_losses": max_consec_losses,
            "max_consec_wins": max_consec_wins,
            "final_capital": capital,
            "max_dd_val": max_dd_val,
            "max_dd_pct": max_dd_pct,
            "roi": roi
        }

    # Ejecutar simulaciones
    p4_ids = ["lotto_activo", "la_granjita", "ruleta_royal", "guacharo_activo"]
    p6_ids = ["lotto_activo", "la_granjita", "ruleta_royal", "guacharo_activo", "guacharito_millonario", "selva_plus"]

    res_p4_cb = run_portfolio_simulation(p4_ids, "Portafolio Anterior (4 Ruletas) [Con Breaker 15]", True)
    res_p4_nocb = run_portfolio_simulation(p4_ids, "Portafolio Anterior (4 Ruletas) [Sin Breaker]", False)

    res_p6_cb = run_portfolio_simulation(p6_ids, "Portafolio Nuevo (6 Ruletas) [Con Breaker 15]", True)
    res_p6_nocb = run_portfolio_simulation(p6_ids, "Portafolio Nuevo (6 Ruletas) [Sin Breaker]", False)

    print(f"{'Métrica':<36} | {'Portafolio 4 (Antiguo)':<24} | {'Portafolio 6 (Nuevo)':<24}")
    print("-" * 90)
    print(f"{'Loterías Incluidas':<36} | {'4 (Lotto,Granj,Roy,Guach)':<24} | {'6 (+Guacharito,Selva)':<24}")
    print(f"{'Total Jugadas Reales (Breaker 15)':<36} | {res_p4_cb['total_plays']:<24,d} | {res_p6_cb['total_plays']:<24,d}")
    print(f"{'Jugadas Ganadas':<36} | {res_p4_cb['total_wins']:<24,d} | {res_p6_cb['total_wins']:<24,d}")
    print(f"{'Jugadas Perdidas':<36} | {res_p4_cb['total_losses']:<24,d} | {res_p6_cb['total_losses']:<24,d}")
    print(f"{'Tasa de Acierto (Win Rate)':<36} | {res_p4_cb['win_rate']:<23.2f}% | {res_p6_cb['win_rate']:<23.2f}%")
    print(f"{'PnL Plano (Unidades)':<36} | {res_p4_cb['flat_pnl']:<+24,.0f} | {res_p6_cb['flat_pnl']:<+24,.0f}")
    print(f"{'Racha Máx Pérdidas (Con Breaker)':<36} | {res_p4_cb['max_consec_losses']:<24d} | {res_p6_cb['max_consec_losses']:<24d}")
    print(f"{'Racha Máx Pérdidas (Sin Breaker)':<36} | {res_p4_nocb['max_consec_losses']:<24d} | {res_p6_nocb['max_consec_losses']:<24d}")
    print(f"{'Racha Máx Ganancias Seguidas':<36} | {res_p4_cb['max_consec_wins']:<24d} | {res_p6_cb['max_consec_wins']:<24d}")
    print(f"{'Drawdown Máximo ($ USD)':<36} | ${res_p4_cb['max_dd_val']:<23,.2f} | ${res_p6_cb['max_dd_val']:<23,.2f}")
    print(f"{'Drawdown Máximo (% del Capital)':<36} | {res_p4_cb['max_dd_pct']:<23.2f}% | {res_p6_cb['max_dd_pct']:<23.2f}%")
    print(f"{'Capital Final ($100 USD Inicial)':<36} | ${res_p4_cb['final_capital']:<23,.2f} | ${res_p6_cb['final_capital']:<23,.2f}")
    print(f"{'Rendimiento Neto (ROI)':<36} | {res_p4_cb['roi']:<+23.2f}% | {res_p6_cb['roi']:<+23.2f}%")

if __name__ == "__main__":
    main()
