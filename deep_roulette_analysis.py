import csv
import math
from collections import Counter, defaultdict

CSV_PATH = r"C:\Users\victo\nuevas_ruletas\casino_data\wiesbaden_100k_spins.csv"

# European wheel pocket order (clockwise)
WHEEL_ORDER = [
    0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10,
    5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26
]
POCKET_INDEX = {num: idx for idx, num in enumerate(WHEEL_ORDER)}

# Sectors
VOISINS = {22, 18, 29, 7, 28, 12, 35, 3, 26, 0, 32, 15, 19, 4, 21, 2, 25} # 17 numbers (45.95%)
TIERS = {27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33} # 12 numbers (32.43%)
ORPHELINS = {1, 20, 14, 31, 9, 17, 34, 6} # 8 numbers (21.62%)
JEU_ZERO = {12, 35, 3, 26, 0, 32, 15} # 7 numbers (18.92%)

def load_data():
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def analyze():
    rows = load_data()
    total = len(rows)
    print(f"Total spins: {total:,}")

    # Breakdown by table
    by_table = defaultdict(list)
    for r in rows:
        by_table[r["table"]].append(r)

    print("\n=== 1. ANALISIS POR MESA ===")
    for t, t_rows in sorted(by_table.items()):
        cnt = len(t_rows)
        nums = [int(r["number"]) for r in t_rows]
        d2 = sum(1 for n in nums if 13 <= n <= 24)
        pct_d2 = d2 / cnt * 100
        z_d2 = (d2 - cnt * (12/37)) / math.sqrt(cnt * (12/37) * (25/37))
        zeros = sum(1 for n in nums if n == 0)
        pct_zero = zeros / cnt * 100
        print(f"Mesa {t:5s}: {cnt:6,d} giros | 2da Docena: {pct_d2:5.2f}% (Z={z_d2:+5.2f}) | Cero: {pct_zero:4.2f}%")

    print("\n=== 2. ANALISIS DE SECTORES FISICOS DE LA RUEDA (TOTAL) ===")
    voisins_cnt = sum(1 for r in rows if int(r["number"]) in VOISINS)
    tiers_cnt = sum(1 for r in rows if int(r["number"]) in TIERS)
    orphelins_cnt = sum(1 for r in rows if int(r["number"]) in ORPHELINS)
    jeuzero_cnt = sum(1 for r in rows if int(r["number"]) in JEU_ZERO)

    print(f"Voisins du Zero (17 nums, teo 45.95%): {voisins_cnt:,} ({voisins_cnt/total*100:.2f}%)")
    print(f"Tiers du Cylindre (12 nums, teo 32.43%): {tiers_cnt:,} ({tiers_cnt/total*100:.2f}%)")
    print(f"Orphelins (8 nums, teo 21.62%): {orphelins_cnt:,} ({orphelins_cnt/total*100:.2f}%)")
    print(f"Jeu Zero (7 nums, teo 18.92%): {jeuzero_cnt:,} ({jeuzero_cnt/total*100:.2f}%)")

    print("\n=== 3. ANALISIS DE DISTANCIA FISICA (ROTOR DELTA) EN GIROS CONSECUTIVOS ===")
    # Para cada mesa consecutiva dentro del mismo dia
    deltas = Counter()
    for t, t_rows in by_table.items():
        # agrupar por dia
        by_day = defaultdict(list)
        for r in t_rows:
            by_day[r["date"]].append(int(r["number"]))
        for day, d_nums in by_day.items():
            for i in range(len(d_nums) - 1):
                idx1 = POCKET_INDEX[d_nums[i]]
                idx2 = POCKET_INDEX[d_nums[i+1]]
                delta = (idx2 - idx1) % 37  # distancia en casillas hacia adelante
                deltas[delta] += 1

    total_deltas = sum(deltas.values())
    print(f"Total transiciones consecutivas analizadas: {total_deltas:,}")
    expected_per_delta = total_deltas / 37
    print(f"Frecuencia teorica esperada por casilla delta: {expected_per_delta:.1f} ({100/37:.2f}%)")
    
    sorted_deltas = sorted(deltas.items(), key=lambda x: x[1], reverse=True)
    print("\nTop 5 deltas fisicos mas repetidos:")
    for delta, count in sorted_deltas[:5]:
        pct = count / total_deltas * 100
        z = (count - expected_per_delta) / math.sqrt(expected_per_delta * (36/37))
        print(f"  Delta +{delta:2d} casillas: {count:5,d} ({pct:.2f}%, Z={z:+.2f})")

    print("\nTop 5 deltas fisicos menos repetidos:")
    for delta, count in sorted_deltas[-5:]:
        pct = count / total_deltas * 100
        z = (count - expected_per_delta) / math.sqrt(expected_per_delta * (36/37))
        print(f"  Delta +{delta:2d} casillas: {count:5,d} ({pct:.2f}%, Z={z:+.2f})")

    print("\n=== 4. ANALISIS DE RETRASOS (SLEEPERS / FALLOS CONSECUTIVOS) ===")
    # Evaluemos docenas y columnas: cual es la distribucion de fallos?
    # Para Docenas (prob de acierto 12/37 = 32.43%, prob fallo = 67.57%)
    doz_misses = {"Dozen 1": [], "Dozen 2": [], "Dozen 3": []}
    curr_miss = {"Dozen 1": 0, "Dozen 2": 0, "Dozen 3": 0}

    for r in rows:
        d = r["dozen"]
        for k in ["Dozen 1", "Dozen 2", "Dozen 3"]:
            if d == k:
                doz_misses[k].append(curr_miss[k])
                curr_miss[k] = 0
            else:
                curr_miss[k] += 1

    for k in ["Dozen 1", "Dozen 2", "Dozen 3"]:
        m_list = doz_misses[k]
        max_m = max(m_list) if m_list else 0
        avg_m = sum(m_list) / len(m_list) if m_list else 0
        print(f"{k}: Promedio de fallos antes de acierto = {avg_m:.2f} | Fallo maximo historico = {max_m}")

if __name__ == "__main__":
    analyze()
