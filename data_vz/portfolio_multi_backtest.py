import numpy as np
import pandas as pd
from datetime import datetime

def run_combined_portfolio_backtest():
    configs = {
        "Lotto Activo": {
            "file": "lotto_activo_2anios.csv",
            "payout": 30.0,
            "lags": [14, 15, 18, 20],
            "k": 38
        },
        "La Granjita": {
            "file": "la_granjita_2anios.csv",
            "payout": 30.0,
            "lags": [14, 15, 17],
            "k": 38
        },
        "Ruleta Royal": {
            "file": "ruleta_royal_2anios.csv",
            "payout": 30.0,
            "lags": [16, 19, 21, 23],
            "k": 37
        },
        "Guacharo Activo": {
            "file": "guacharo_activo_2anios.csv",
            "payout": 60.0,
            "lags": [25, 31, 41, 42],
            "k": 77
        }
    }

    # Cargar y unir todos los sorteos en una línea temporal única
    all_events = []
    for lotto_name, cfg in configs.items():
        df = pd.read_csv(cfg["file"], encoding="utf-8-sig", dtype={"numero": str})
        df["loteria"] = lotto_name
        df["payout"] = cfg["payout"]
        df["dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        df = df.dropna(subset=["dt"]).copy()
        for _, row in df.iterrows():
            all_events.append({
                "dt": row["dt"],
                "fecha": row["fecha"],
                "hora": row["hora"],
                "loteria": lotto_name,
                "numero": str(row["numero"]),
                "animal": str(row["animal"])
            })

    # Ordenar estrictamente por fecha y hora
    all_events.sort(key=lambda x: x["dt"])
    print(f"Total eventos combinados en el cronograma unificado: {len(all_events):,} sorteos.")
    print(f"Desde: {all_events[0]['fecha']} hasta {all_events[-1]['fecha']}\n")

    # Probaremos dos niveles de gestión de riesgo sobre el capital unificado de 100 $:
    # Nivel 1: Moderado (0.3% del capital por animal)
    # Nivel 2: Agresivo (0.5% del capital por animal)
    
    simulations = [
        ("PERFIL MODERADO (0.30% por animal / ~1% a 1.2% por jugada)", 0.003),
        ("PERFIL AGRESIVO (0.50% por animal / ~1.5% a 2.0% por jugada)", 0.005)
    ]

    for sim_title, bet_fraction in simulations:
        # Estado individual de cada ruleta
        history_nums = {name: [] for name in configs}
        streaks = {name: 0 for name in configs}
        
        # Estado del Banco Compartido
        init_capital = 100.0
        bankroll = init_capital
        peak = init_capital
        max_dd_usd = 0.0
        max_dd_pct = 0.0
        
        # Estadísticas individuales
        stats_by_lotto = {name: {'bets': 0, 'hits': 0, 'pnl_usd': 0.0} for name in configs}
        
        total_bets_placed = 0
        total_hits = 0
        
        # Historial de equity diario
        equity_curve = []
        date_curve = []

        for ev in all_events:
            lotto = ev["loteria"]
            num = ev["numero"]
            l_cfg = configs[lotto]
            payout = l_cfg["payout"]
            lags = l_cfg["lags"]
            max_lag_needed = max(lags)
            
            h_list = history_nums[lotto]
            cur_streak = streaks[lotto]
            
            # Verificar si tenemos suficiente historial para esa ruleta
            can_evaluate = len(h_list) >= (max_lag_needed + 6)
            
            cands = []
            if can_evaluate:
                rec6 = set(h_list[-6:])
                raw_cands = {h_list[-l] for l in lags}
                cands = list(raw_cands - rec6)
                
            hit = (num in cands) if cands else False
            cost_units = len(cands)
            
            # ¿Se activa el gatillo? (Racha previa del sistema en esta lotería == 1)
            if can_evaluate and cur_streak == 1 and cost_units > 0:
                bet_per_animal = bankroll * bet_fraction
                total_cost = bet_per_animal * cost_units
                
                # Proteger contra sobre-exposición
                if total_cost >= bankroll:
                    total_cost = bankroll * 0.95
                    bet_per_animal = total_cost / cost_units
                    
                total_bets_placed += cost_units
                stats_by_lotto[lotto]['bets'] += cost_units
                
                if hit:
                    total_hits += 1
                    stats_by_lotto[lotto]['hits'] += 1
                    gain = bet_per_animal * payout - total_cost
                    bankroll += gain
                    stats_by_lotto[lotto]['pnl_usd'] += gain
                else:
                    bankroll -= total_cost
                    stats_by_lotto[lotto]['pnl_usd'] -= total_cost
                    
                if bankroll > peak:
                    peak = bankroll
                dd_usd = peak - bankroll
                dd_pct = (dd_usd / peak) * 100 if peak > 0 else 0
                if dd_usd > max_dd_usd:
                    max_dd_usd = dd_usd
                if dd_pct > max_dd_pct:
                    max_dd_pct = dd_pct
                    
                equity_curve.append(bankroll)
                date_curve.append(ev["fecha"])

            # Actualizar racha virtual de esta ruleta específica
            if can_evaluate and cost_units > 0:
                if hit:
                    streaks[lotto] = 0
                else:
                    streaks[lotto] += 1
                    
            # Agregar al historial de esta ruleta
            h_list.append(num)

        mult = bankroll / init_capital
        net_profit = bankroll - init_capital
        cagr = (mult ** (1.0 / 2.0) - 1.0) * 100

        print("=" * 100)
        print(f" {sim_title}")
        print("=" * 100)
        print(f"• Capital Inicial Compartido:      $100.00 USD")
        print(f"• Capital Final Acumulado (HOY):   ${bankroll:,.2f} USD")
        print(f"• Ganancia Neta Total:             +${net_profit:,.2f} USD")
        print(f"• Multiplicador de Cuenta:         {mult:,.2f}x veces el capital inicial")
        print(f"• Rendimiento Anual Compuesto:     +{cagr:,.1f}% anual")
        print(f"• Drawdown Máximo Combinado:       -{max_dd_pct:.2f}% (-${max_dd_usd:,.2f} USD)")
        print(f"• Total Fichas Apostadas:          {total_bets_placed:,} fichas en 2 años")
        print(f"• Total Aciertos Globales:         {total_hits:,} aciertos\n")

        print("  DESGLOSE POR RULETA (Aporte de cada una al banco compartido):")
        print(f"  {'Ruleta':<18} | {'Fichas Apostadas':<18} | {'Aciertos':<10} | {'Win Rate Sorteo':<16} | {'Aporte Neto en USD'}")
        print("  " + "-" * 88)
        for l_name, st in stats_by_lotto.items():
            wr = (st['hits'] / (st['bets'] / (len(configs[l_name]['lags']))) * 100) if st['bets'] > 0 else 0
            print(f"  {l_name:<18} | {st['bets']:<18,d} | {st['hits']:<10,d} | {wr:>6.2f}%          | +${st['pnl_usd']:>12,.2f} USD")

        # Evolución semestral
        df_eq = pd.DataFrame({'fecha': date_curve, 'equity': equity_curve})
        df_eq['dt'] = pd.to_datetime(df_eq['fecha'])
        df_eq = df_eq.set_index('dt')
        res_6m = df_eq['equity'].resample('6ME').last().dropna()
        
        print("\n  EVOLUCIÓN TEMPORAL DEL BANCO COMPARTIDO:")
        print(f"    - Inicio (Octubre 2024):    $    100.00 USD")
        for dt_v, v in res_6m.items():
            print(f"    - {dt_v.strftime('%B %Y'):<24}: ${v:>10,.2f} USD")
        print("\n")

if __name__ == "__main__":
    run_combined_portfolio_backtest()
