import numpy as np
import pandas as pd

def inspect_exact_sniper_streaks():
    configs = {
        "Lotto Activo": {
            "file": "lotto_activo_2anios.csv",
            "payout": 30.0,
            "lags": [14, 15, 18, 20],
        },
        "La Granjita": {
            "file": "la_granjita_2anios.csv",
            "payout": 30.0,
            "lags": [14, 15, 17],
        },
        "Ruleta Royal": {
            "file": "ruleta_royal_2anios.csv",
            "payout": 30.0,
            "lags": [16, 19, 21, 23],
        },
        "Guacharo Activo": {
            "file": "guacharo_activo_2anios.csv",
            "payout": 60.0,
            "lags": [25, 31, 41, 42],
        }
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

    # 1. Simulación individual de cada ruleta para ver sus rachas aisladas
    print("=========================================================================================")
    print(" RACHAS DE APUESTAS REALES PERDIDAS POR SEPARADO (CADA RULETA AISLADA)")
    print("=========================================================================================\n")

    for lotto_name, cfg in configs.items():
        df_l = pd.read_csv(cfg["file"], encoding="utf-8-sig", dtype={"numero": str})
        df_l["dt"] = pd.to_datetime(df_l["fecha"] + " " + df_l["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        df_l = df_l.dropna(subset=["dt"]).sort_values(by="dt").reset_index(drop=True)
        
        nums = df_l["numero"].tolist()
        lags = cfg["lags"]
        max_l = max(lags)
        
        real_bets = [] # solo apuestas con dinero real
        streak = 0
        for i in range(max_l + 6, len(nums)):
            actual = nums[i]
            rec6 = set(nums[i-6:i])
            cands = list({nums[i-l] for l in lags} - rec6)
            hit = (actual in cands)
            cost = len(cands)
            
            # Si racha == 1, se dispara apuesta real
            if streak == 1 and cost > 0:
                real_bets.append(hit)
                
            if cost > 0:
                if hit:
                    streak = 0
                else:
                    streak += 1
                    
        # Calcular rachas de apuestas reales falladas consecutivas
        loss_runs = []
        cur_l = 0
        for b in real_bets:
            if not b:
                cur_l += 1
            else:
                if cur_l > 0:
                    loss_runs.append(cur_l)
                    cur_l = 0
        if cur_l > 0:
            loss_runs.append(cur_l)
            
        m_loss = max(loss_runs) if loss_runs else 0
        avg_loss = np.mean(loss_runs) if loss_runs else 0
        tot_bets = len(real_bets)
        tot_wins = sum(real_bets)
        win_rate = (tot_wins / tot_bets * 100) if tot_bets > 0 else 0
        
        print(f"[{lotto_name.upper()}]")
        print(f"  • Total apuestas reales disparadas:          {tot_bets:,}")
        print(f"  • Apuestas GANADAS (Aciertos):               {tot_wins} ({win_rate:.2f}%)")
        print(f"  • Apuestas PERDIDAS:                         {tot_bets - tot_wins}")
        print(f"  • MÁXIMAS APUESTAS REALES FALLADAS SEGUIDAS: {m_loss} apuestas consecutivas")
        print(f"  • Promedio de apuestas falladas entre aciertos: {avg_loss:.1f} apuestas")
        print()

    # 2. Portafolio Paralelizado
    history = {k: [] for k in configs}
    streaks = {k: 0 for k in configs}
    parallel_real_bets = []

    for ev in all_events:
        lotto = ev["loteria"]
        num = ev["numero"]
        lags = configs[lotto]["lags"]
        h = history[lotto]
        can_eval = len(h) >= (max(lags) + 6)
        
        cands = []
        if can_eval:
            rec6 = set(h[-6:])
            cands = list({h[-l] for l in lags} - rec6)
            
        hit = (num in cands) if cands else False
        cost = len(cands)
        
        if can_eval and streaks[lotto] == 1 and cost > 0:
            parallel_real_bets.append({
                "dt": ev["dt"],
                "loteria": lotto,
                "hit": hit
            })
            
        if can_eval and cost > 0:
            if hit:
                streaks[lotto] = 0
            else:
                streaks[lotto] += 1
        h.append(num)

    # Analizar la racha de 76 pérdidas en paralelo: ¿Cuándo ocurrió y de qué loterías estuvo compuesta?
    consec = []
    current_run = []
    all_runs = []
    
    for b in parallel_real_bets:
        if not b["hit"]:
            current_run.append(b)
        else:
            if current_run:
                all_runs.append(current_run)
                current_run = []
    if current_run:
        all_runs.append(current_run)
        
    longest_run = max(all_runs, key=len)
    
    print("=========================================================================================")
    print(" DETALLE DE LA PEOR RACHA EN PARALELO (76 APUESTAS REALES PERDIDAS)")
    print("=========================================================================================")
    print(f"• Longitud: {len(longest_run)} apuestas reales consecutivas sin acertar")
    print(f"• Fecha Inicio: {longest_run[0]['dt'].strftime('%Y-%m-%d %I:%M %p')}")
    print(f"• Fecha Fin:    {longest_run[-1]['dt'].strftime('%Y-%m-%d %I:%M %p')}")
    
    # Composición por lotería de esa racha
    df_worst = pd.DataFrame(longest_run)
    print("\n• ¿De qué ruletas provinieron los tiros de esa racha?")
    print(df_worst['loteria'].value_counts())
    print("=========================================================================================\n")

if __name__ == "__main__":
    inspect_exact_sniper_streaks()
