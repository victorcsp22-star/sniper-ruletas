import pandas as pd
import numpy as np
import scipy.stats as stats

def test_all_patterns():
    csv_file = "C:/Users/victo/nuevas_ruletas/lotto_activo_rd_lotoven_completo.csv"
    df = pd.read_csv(csv_file, dtype={"numero": str})
    
    hora_order = {
        "08:30 AM": 1, "09:30 AM": 2, "10:30 AM": 3, "11:30 AM": 4,
        "12:30 PM": 5, "01:30 PM": 6, "02:30 PM": 7, "03:30 PM": 8,
        "04:30 PM": 9, "05:30 PM": 10, "06:30 PM": 11, "07:30 PM": 12
    }
    df["h_rank"] = df["hora"].map(hora_order)
    df = df.sort_values(by=["fecha", "h_rank"]).reset_index(drop=True)
    
    nums = df["numero"].tolist()
    dates = df["fecha"].tolist()
    hours = df["h_rank"].tolist()
    N = len(nums)
    split_idx = int(N * 0.70)
    
    canon_animals = [
        "0", "00", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
        "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
        "21", "22", "23", "24", "25", "26", "27", "28", "29", "30",
        "31", "32", "33", "34", "35", "36"
    ]
    
    # 1. Aprender Markov en In-Sample
    trans = {}
    tot_trans = {}
    for i in range(split_idx - 1):
        a, b = nums[i], nums[i+1]
        trans[(a, b)] = trans.get((a, b), 0) + 1
        tot_trans[a] = tot_trans.get(a, 0) + 1
        
    markov_pairs = {}
    for (a, b), cnt in trans.items():
        if tot_trans[a] >= 30:
            r = cnt / tot_trans[a]
            p = stats.binomtest(cnt, tot_trans[a], 1/38, alternative='greater').pvalue
            if r > 1/30 and p < 0.05:
                if a not in markov_pairs: markov_pairs[a] = []
                markov_pairs[a].append(b)

    # Precomputar el estado del Gatillo Sniper sobre los Lags [21, 39, 50] a lo largo de TODA la historia
    lags = [21, 39, 50]
    sniper_triggers = [False] * N
    base_streak = 0
    for i in range(max(lags) + 6, N):
        rec6 = set(nums[i-6:i])
        cands = list(set([nums[i-l] for l in lags if i >= l]) - rec6)
        if cands:
            hit = (nums[i] in cands)
            if base_streak == 1:
                sniper_triggers[i] = True
            base_streak = 0 if hit else base_streak + 1
        else:
            base_streak = 0

    def simulate(name, selector_func):
        cap = 200.0
        bets = 0
        wins = 0
        losses = 0
        mdd = 0.0
        peak = 200.0
        
        seen_today = set()
        current_date = None
        
        last_seen = {a: -999 for a in canon_animals}
        for i in range(split_idx):
            last_seen[nums[i]] = i

        for i in range(split_idx, N):
            actual = nums[i]
            prev = nums[i-1]
            d = dates[i]
            h = hours[i]
            
            if d != current_date:
                current_date = d
                seen_today = set()
                
            targets = selector_func(i, prev, h, seen_today, last_seen, sniper_triggers[i])
            
            for t in targets:
                if cap < 1.0:
                    break
                bets += 1
                if t == actual:
                    wins += 1
                    cap += 29.0
                else:
                    losses += 1
                    cap -= 1.0
                if cap > peak:
                    peak = cap
                dd = peak - cap
                if dd > mdd:
                    mdd = dd
                    
            seen_today.add(actual)
            last_seen[actual] = i
            
        win_rate = (wins / bets * 100.0) if bets > 0 else 0
        pf = (wins * 29.0) / losses if losses > 0 else 0
        roi = ((cap - 200.0) / bets * 100.0) if bets > 0 else 0
        net = cap - 200.0
        
        return {
            "name": name,
            "cap": cap,
            "net": net,
            "bets": bets,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "pf": pf,
            "roi": roi,
            "mdd": mdd
        }

    # 1. Gatillo Sniper Clásico (Post-Fallo 1 en Lags 21, 39, 50)
    def s1(i, prev, h, seen_today, last_seen, is_sniper):
        if is_sniper:
            rec6 = set(nums[i-6:i])
            return list(set([nums[i-l] for l in lags if i >= l]) - rec6)
        return []

    # 2. Cadenas de Markov Puras (A -> B sin filtro)
    def s2(i, prev, h, seen_today, last_seen, is_sniper):
        return markov_pairs.get(prev, [])

    # 3. Matriz 6x6 (Rebote de Fila: si salió F, apostar a 2 de su fila no recientes)
    matrix_grid = {
        "1": 1, "2": 1, "3": 1, "4": 1, "5": 1, "6": 1,
        "7": 2, "8": 2, "9": 2, "10": 2, "11": 2, "12": 2,
        "13": 3, "14": 3, "15": 3, "16": 3, "17": 3, "18": 3,
        "19": 4, "20": 4, "21": 4, "22": 4, "23": 4, "24": 4,
        "25": 5, "26": 5, "27": 5, "28": 5, "29": 5, "30": 5,
        "31": 6, "32": 6, "33": 6, "34": 6, "35": 6, "36": 6,
        "0": 0, "00": 0
    }
    def s3(i, prev, h, seen_today, last_seen, is_sniper):
        f = matrix_grid.get(prev, 0)
        if f == 0: return []
        row_animals = [a for a, rf in matrix_grid.items() if rf == f]
        rec6 = set(nums[i-6:i])
        return [a for a in row_animals if a not in rec6][:2]

    # 4. Atrasos Extremos (Animal más frío > 75 sorteos)
    def s4(i, prev, h, seen_today, last_seen, is_sniper):
        droughts = {a: (i - last_seen[a]) for a in canon_animals}
        top_cold = sorted(droughts.items(), key=lambda x: x[1], reverse=True)
        if top_cold[0][1] >= 75:
            return [top_cold[0][0]]
        return []

    # 5. Represión Intradía + Markov (Sorteos >= 10: 05:30 a 07:30 PM)
    def s5(i, prev, h, seen_today, last_seen, is_sniper):
        if h >= 10:
            cands = markov_pairs.get(prev, [])
            return [c for c in cands if c not in seen_today]
        return []

    # 6. Represión Intradía + Markov Final (Sorteos >= 11: 06:30 y 07:30 PM)
    def s6(i, prev, h, seen_today, last_seen, is_sniper):
        if h >= 11:
            cands = markov_pairs.get(prev, [])
            return [c for c in cands if c not in seen_today]
        return []

    # 7. Confluencia Sniper + Represión Intradía (Gatillo Sniper activo Y candidato NO ha salido hoy)
    def s7(i, prev, h, seen_today, last_seen, is_sniper):
        if is_sniper and h >= 9:
            rec6 = set(nums[i-6:i])
            cands = list(set([nums[i-l] for l in lags if i >= l]) - rec6 - seen_today)
            return cands
        return []

    strats = [
        ("Patrón 1: Gatillo Sniper Post-Fallo 1 (Lags 21, 39, 50)", s1),
        ("Patrón 2: Cadenas de Markov Puras (A -> B sin filtro)  ", s2),
        ("Patrón 3: Matriz 6x6 (Rebote de Fila / Vecindad)       ", s3),
        ("Patrón 4: Atrasos Extremos (Rebote Animal Frío >75)    ", s4),
        ("Patrón 5: Represión Intradía Tardía (Sorteos >= 10)    ", s5),
        ("Patrón 6: Represión Intradía Final  (Sorteos >= 11)    ", s6),
        ("Patrón 7: Confluencia Sniper + Represión Intradía      ", s7),
    ]

    print("="*85)
    print("COMPARATIVA FORENSE DE TODOS LOS PATRONES: $200 USD INVERSIÓN PLANA")
    print("Lotto Activo RD Internacional | Muestra Fuera de Muestra: 5,789 sorteos | Pago: 30x")
    print("="*85)
    
    for name, f in strats:
        r = simulate(name, f)
        print(f"\n>>> {r['name']}")
        print(f"  Capital Final:   ${r['cap']:.2f} USD  ({r['net']:+.2f} USD)")
        print(f"  Total Apuestas:  {r['bets']}  (Aciertos: {r['wins']}, Fallos: {r['losses']})")
        print(f"  Tasa de Acierto: {r['win_rate']:.3f}% (Break-even necesario: 3.333%)")
        print(f"  Profit Factor:   {r['pf']:.2f}")
        print(f"  Retorno (ROI):   {r['roi']:+.2f}%")
        print(f"  Max Drawdown:    ${r['mdd']:.2f} USD")
        print(f"  ¿Sobrevivió?     {'SÍ (Capital intacto)' if r['cap'] > 0 else 'NO (Bancarrota a $0)'}")

if __name__ == "__main__":
    test_all_patterns()
