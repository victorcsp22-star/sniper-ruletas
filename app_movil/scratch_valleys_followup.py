import csv, statistics

with open(r"C:\Users\victo\nuevas_ruletas\ledger_nuevas_ruletas.csv", "r", encoding="utf-8", errors="ignore") as f:
    rows = list(csv.DictReader(f))

deep_valleys = []
cur_streak = 0
for i, r in enumerate(rows):
    cob = float(r.get("cobrado", 0.0) or 0.0)
    pnl = float(r.get("pnl", 0.0) or 0.0)
    if cob > 0 or pnl > 0:
        if cur_streak >= 19:
            deep_valleys.append((i, cur_streak))
        cur_streak = 0
    else:
        cur_streak += 1

print(f"Total valles profundos (>= 19 fallos) encontrados: {len(deep_valleys)}")

distancias = []
for idx, (win_idx, length) in enumerate(deep_valleys, 1):
    w1 = rows[win_idx]
    next_win_dist = None
    w2 = None
    for j in range(win_idx + 1, len(rows)):
        c2 = float(rows[j].get("cobrado", 0.0) or 0.0)
        p2 = float(rows[j].get("pnl", 0.0) or 0.0)
        if c2 > 0 or p2 > 0:
            next_win_dist = j - win_idx
            w2 = rows[j]
            break
    
    fec1 = w1.get("fecha")
    hor1 = w1.get("hora")
    rul1 = w1.get("ruleta")
    cob1 = w1.get("cobrado")
    print(f"\n--- VALLE #{idx}: Duró {length} fallos ---")
    print(f"  1er Acierto: {fec1} {hor1} en {rul1} | Cobro: ${cob1}")
    if next_win_dist is not None:
        fec2 = w2.get("fecha")
        hor2 = w2.get("hora")
        rul2 = w2.get("ruleta")
        cob2 = w2.get("cobrado")
        distancias.append(next_win_dist)
        print(f"  2do Acierto: A los {next_win_dist} tiros -> {fec2} {hor2} en {rul2} | Cobro: ${cob2}")
    else:
        print("  (Aún no hay segundo acierto posterior)")

if distancias:
    print(f"\nDISTANCIA PROMEDIO AL SEGUNDO ACIERTO: {statistics.mean(distancias):.1f} disparos")
    print(f"MEDIANA DE DISTANCIA: {statistics.median(distancias)} disparos")
    print(f"DISTANCIA MÍNIMA: {min(distancias)} tiros | MÁXIMA: {max(distancias)} tiros")
