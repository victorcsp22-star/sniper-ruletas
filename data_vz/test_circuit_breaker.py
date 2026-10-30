import pandas as pd
import numpy as np

def test_circuit_breaker():
    configs = {
        "Lotto Activo": {"file": "lotto_activo_2anios.csv", "payout": 30.0, "lags": [14, 15, 18, 20]},
        "La Granjita": {"file": "la_granjita_2anios.csv", "payout": 30.0, "lags": [14, 15, 17]},
        "Ruleta Royal": {"file": "ruleta_royal_2anios.csv", "payout": 30.0, "lags": [16, 19, 21, 23]},
        "Guacharo Activo": {"file": "guacharo_activo_2anios.csv", "payout": 60.0, "lags": [25, 31, 41, 42]}
    }

    all_events = []
    for lotto_name, cfg in configs.items():
        df = pd.read_csv(cfg["file"], encoding="utf-8-sig", dtype={"numero": str})
        df["loteria"] = lotto_name
        df["dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        for _, row in df.dropna(subset=["dt"]).iterrows():
            all_events.append({
                "dt": row["dt"],
                "fecha": row["fecha"],
                "hora": row["hora"],
                "loteria": lotto_name,
                "numero": str(row["numero"])
            })

    all_events.sort(key=lambda x: x["dt"])

    # Probar diferentes límites de freno de emergencia (Circuit Breaker):
    # Sin freno vs Freno a los 15 fallos seguidos vs Freno a los 20 fallos
    for max_consec_limit in [999, 20, 15]:
        bankroll = 100.0
        peak = 100.0
        max_dd = 0.0
        history = {k: [] for k in configs}
        streaks = {k: 0 for k in configs}
        
        consec_losses_portfolio = 0
        max_real_loss_seen = 0
        paused = False
        
        real_bets = 0
        real_hits = 0
        
        for ev in all_events:
            lotto = ev["loteria"]
            num = ev["numero"]
            lags = configs[lotto]["lags"]
            payout = configs[lotto]["payout"]
            h = history[lotto]
            can_eval = len(h) >= (max(lags) + 6)
            
            cands = []
            if can_eval:
                rec6 = set(h[-6:])
                cands = list({h[-l] for l in lags} - rec6)
                
            hit = (num in cands) if cands else False
            cost = len(cands)
            
            # Si el portafolio está pausado por freno de emergencia, se reanuda cuando CUALQUIERA acierte en papel
            if paused:
                if hit:
                    paused = False
                    consec_losses_portfolio = 0
                    
            # Si no está pausado y la ruleta tiene gatillo activo
            is_betting = (can_eval and streaks[lotto] == 1 and cost > 0 and not paused)
            
            if is_betting:
                real_bets += 1
                bet_anim = bankroll * 0.0020 # 0.20%
                c_tot = bet_anim * cost
                
                if hit:
                    real_hits += 1
                    bankroll += (bet_anim * payout - c_tot)
                    consec_losses_portfolio = 0
                else:
                    bankroll -= c_tot
                    consec_losses_portfolio += 1
                    if consec_losses_portfolio > max_real_loss_seen:
                        max_real_loss_seen = consec_losses_portfolio
                    if consec_losses_portfolio >= max_consec_limit:
                        paused = True # ¡FRENO DE EMERGENCIA ACTIVADO!
                        
                if bankroll > peak: peak = bankroll
                dd = (peak - bankroll) / peak * 100
                if dd > max_dd: max_dd = dd
                
            if can_eval and cost > 0:
                streaks[lotto] = 0 if hit else (streaks[lotto] + 1)
            h.append(num)
            
        label = "Sin Freno (Original)" if max_consec_limit == 999 else f"Freno tras {max_consec_limit} fallos"
        print(f"[{label}]")
        print(f"  • Máxima racha de pérdidas seguidas: {max_real_loss_seen} apuestas")
        print(f"  • Capital Final ($100 inicial):       ${bankroll:,.2f} USD")
        print(f"  • Drawdown Máximo:                    -{max_dd:.1f}%")
        print(f"  • Apuestas realizadas:                {real_bets:,} (Aciertos: {real_hits})")
        print()

if __name__ == "__main__":
    test_circuit_breaker()
