import pandas as pd

def print_76_bets():
    configs = {
        "Lotto Activo": {"file": "lotto_activo_2anios.csv", "payout": 30.0, "lags": [14, 15, 18, 20]},
        "La Granjita": {"file": "la_granjita_2anios.csv", "payout": 30.0, "lags": [14, 15, 17]},
        "Ruleta Royal": {"file": "ruleta_royal_2anios.csv", "payout": 30.0, "lags": [16, 19, 21, 23]},
        "Guacharo Activo": {"file": "guacharo_activo_2anios.csv", "payout": 60.0, "lags": [25, 31, 41, 42]}
    }

    all_events = []
    for lotto_name, cfg in configs.items():
        df = pd.read_csv(cfg["file"], encoding="utf-8-sig", dtype={"numero": str})
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

    history = {k: [] for k in configs}
    streaks = {k: 0 for k in configs}
    real_bets = []

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
            real_bets.append({
                "dt": ev["dt"],
                "loteria": lotto,
                "numero": num,
                "cands": cands,
                "hit": hit
            })
            
        if can_eval and cost > 0:
            if hit:
                streaks[lotto] = 0
            else:
                streaks[lotto] += 1
        h.append(num)

    # Let's inspect the longest loss streak in real_bets
    current_run = []
    runs = []
    for b in real_bets:
        if not b["hit"]:
            current_run.append(b)
        else:
            if current_run:
                runs.append(current_run)
                current_run = []
    if current_run:
        runs.append(current_run)

    longest = max(runs, key=len)
    print(f"Total apuestas reales en el portafolio: {len(real_bets)}")
    print(f"Total aciertos reales: {sum(1 for b in real_bets if b['hit'])}")
    print(f"Longest loss streak: {len(longest)} apuestas")
    print(f"Start: {longest[0]['dt']} | End: {longest[-1]['dt']}")
    
    # Check the 5 bets before the streak and 5 bets after
    start_idx = real_bets.index(longest[0])
    end_idx = real_bets.index(longest[-1])
    
    print("\nApuesta ganadora inmediatamente ANTERIOR a la racha:")
    prev_bet = real_bets[start_idx - 1]
    print(f"  {prev_bet['dt']} | {prev_bet['loteria']} | Salió {prev_bet['numero']} en {prev_bet['cands']} -> HIT = {prev_bet['hit']}")
    
    print("\nApuesta ganadora inmediatamente POSTERIOR a la racha:")
    next_bet = real_bets[end_idx + 1]
    print(f"  {next_bet['dt']} | {next_bet['loteria']} | Salió {next_bet['numero']} en {next_bet['cands']} -> HIT = {next_bet['hit']}")
    
    print(f"\nDurante esas {len(longest)} apuestas intermedias:")
    by_lotto = pd.DataFrame(longest)["loteria"].value_counts()
    print(by_lotto)

if __name__ == "__main__":
    print_76_bets()
