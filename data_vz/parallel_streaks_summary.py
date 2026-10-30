import numpy as np
import pandas as pd

def compute_streak_metrics_parallel():
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

    # Simular la secuencia de jugadas reales en el cronograma unificado
    history = {k: [] for k in configs}
    streaks = {k: 0 for k in configs}

    # Registro de todas las jugadas reales
    # Cada entrada representa un sorteo donde el bot disparó una apuesta
    real_plays = []

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
        
        # ¿Dispara Gatillo 1?
        if can_eval and streaks[lotto] == 1 and cost > 0:
            real_plays.append({
                "dt": ev["dt"],
                "fecha": ev["fecha"],
                "hora": ev["hora"],
                "loteria": lotto,
                "hit": hit,
                "cost_fichas": cost,
                "payout": payout,
                "net_fichas": (payout - cost) if hit else -cost
            })

        if can_eval and cost > 0:
            if hit:
                streaks[lotto] = 0
            else:
                streaks[lotto] += 1
                
        h.append(num)

    df_plays = pd.DataFrame(real_plays)
    total_plays = len(df_plays)
    total_wins = df_plays["hit"].sum()
    total_losses = total_plays - total_wins
    
    total_fichas_apostadas = df_plays["cost_fichas"].sum()
    total_fichas_ganadas = sum(r["payout"] for _, r in df_plays.iterrows() if r["hit"])
    pnl_fichas = df_plays["net_fichas"].sum()

    # Calcular cadenas/rachas consecutivas en el cronograma unificado
    # Racha de pérdidas consecutivas
    loss_streaks = []
    win_streaks = []
    
    cur_loss = 0
    cur_win = 0
    
    for hit in df_plays["hit"]:
        if hit:
            win_streaks.append(cur_loss) # distancia de fallos
            cur_loss = 0
            cur_win += 1
        else:
            if cur_win > 0:
                # guardamos racha de victorias previas
                cur_win = 0
            cur_loss += 1

    # Analizar rachas de victorias consecutivas (ganar 2, 3, etc. sorteos seguidos en el portafolio)
    consec_wins = []
    c_w = 0
    for hit in df_plays["hit"]:
        if hit:
            c_w += 1
        else:
            if c_w > 0:
                consec_wins.append(c_w)
                c_w = 0
    if c_w > 0:
        consec_wins.append(c_w)

    # Analizar rachas de pérdidas consecutivas (fallar 2, 3, etc. sorteos seguidos)
    consec_losses = []
    c_l = 0
    for hit in df_plays["hit"]:
        if not hit:
            c_l += 1
        else:
            if c_l > 0:
                consec_losses.append(c_l)
                c_l = 0
    if c_l > 0:
        consec_losses.append(c_l)

    max_consec_losses = max(consec_losses) if consec_losses else 0
    avg_consec_losses = np.mean(consec_losses) if consec_losses else 0
    
    max_consec_wins = max(consec_wins) if consec_wins else 0
    avg_consec_wins = np.mean(consec_wins) if consec_wins else 0

    print("=========================================================================================")
    print(" MÉTRICAS DE VOLUMEN Y RACHAS CONSECUTIVAS EN PARALELO (2 AÑOS DE HISTORIAL)")
    print("=========================================================================================\n")

    print(f"1. VOLUMEN DE JUGADAS EN PARALELO (Sorteos apostados con dinero real):")
    print(f"   • Total de jugadas / sorteos apostados:    {total_plays:,} sorteos")
    print(f"   • Sorteos GANADOS (Aciertos):             {total_wins:,} sorteos ({total_wins/total_plays*100:.2f}%)")
    print(f"   • Sorteos PERDIDOS (Fallos):               {total_losses:,} sorteos ({total_losses/total_plays*100:.2f}%)")
    print(f"   • Frecuencia de apuesta:                   ~3.5 disparos al día en promedio")
    print()

    print(f"2. VOLUMEN EN FICHAS / ANIMALES INDIVIDUALES:")
    print(f"   • Fichas / Animales apostados en total:    {total_fichas_apostadas:,} fichas")
    print(f"   • Fichas acertadas (ganadoras 30x/60x):    {total_wins:,} aciertos")
    print(f"   • Fichas falladas:                         {total_fichas_apostadas - total_wins:,} fallos")
    print(f"   • Balance neto en fichas:                  +{pnl_fichas:,.0f} fichas de beneficio neto")
    print()

    print(f"3. CADENAS Y RACHAS CONSECUTIVAS EN PARALELO:")
    print(f"   • MÁXIMA CADENA DE PÉRDIDAS CONSECUTIVAS:  {max_consec_losses} sorteos seguidos sin ganar")
    print(f"   • Promedio de fallos entre aciertos:       {avg_consec_losses:.1f} sorteos (~1.9 días)")
    print(f"   • MÁXIMA CADENA DE GANANCIAS CONSECUTIVAS: {max_consec_wins} sorteos seguidos ganando")
    print(f"   • Total veces que ganó 2 seguidas o más:   {sum(1 for w in consec_wins if w >= 2)} ocasiones")
    print(f"   • Total veces que ganó 3 seguidas o más:   {sum(1 for w in consec_wins if w >= 3)} ocasiones")
    print()

    # Distribución de cadenas de pérdidas
    print("4. DISTRIBUCIÓN DE CADENAS DE PÉRDIDAS (¿En cuántos sorteos se corta la racha?):")
    series_losses = pd.Series(consec_losses)
    print(f"   • Rachas cortadas en 1 a 3 sorteos:        {(series_losses <= 3).sum()} veces ({(series_losses <= 3).mean()*100:.1f}%)")
    print(f"   • Rachas cortadas en 4 a 7 sorteos:        {((series_losses >= 4) & (series_losses <= 7)).sum()} veces ({((series_losses >= 4) & (series_losses <= 7)).mean()*100:.1f}%)")
    print(f"   • Rachas cortadas en 8 a 15 sorteos:       {((series_losses >= 8) & (series_losses <= 15)).sum()} veces ({((series_losses >= 8) & (series_losses <= 15)).mean()*100:.1f}%)")
    print(f"   • Rachas largas (> 15 sorteos):            {(series_losses > 15).sum()} veces ({(series_losses > 15).mean()*100:.1f}%)")
    print("=========================================================================================\n")

if __name__ == "__main__":
    compute_streak_metrics_parallel()
