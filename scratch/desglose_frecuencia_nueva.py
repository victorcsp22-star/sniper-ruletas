import os, pandas as pd, collections

CONFIG_NUEVA = {
    "Lotto Gato": (r"C:\Users\victo\nuevas_ruletas\lotto_gato.csv", [18, 38, 14], [1, 2], 6),
    "Loto Chaima": (r"C:\Users\victo\nuevas_ruletas\loto_chaima.csv", [49, 41, 35], [0, 1], 6),
    "Guacharo Activo": (r"C:\Users\victo\nuevas_ruletas\data_vz\guacharo_activo_2anios.csv", [31, 54, 41], [1, 3], 8),
    "Lotto Activo": (r"C:\Users\victo\nuevas_ruletas\data_vz\lotto_activo_2anios.csv", [20, 18, 15], [1, 2], 6),
    "Ruleta Royal": (r"C:\Users\victo\nuevas_ruletas\data_vz\ruleta_royal_2anios.csv", [19, 16, 31], [1], 6),
    "Mega Animal 40": (r"C:\Users\victo\nuevas_ruletas\mega_animal_40.csv", [18, 20, 43], [1, 2, 3], 8),
    "Gatazo": (r"C:\Users\victo\nuevas_ruletas\gatazo.csv", [35, 9, 20], [1], 6),
    "Monje Millonario": (r"C:\Users\victo\nuevas_ruletas\monje_millonario.csv", [24, 42, 48], [0, 1], 6),
    "Granja Mill. Granjazo": (r"C:\Users\victo\nuevas_ruletas\granja_millonaria_granjazo.csv", [45, 26, 15], [1, 3], 6),
}

start_date = "2026-09-15"
end_date = "2026-10-31"

counts_by_roulette = collections.defaultdict(int)

for r_name, (fpath, lags, target_streaks, rec_w) in CONFIG_NUEVA.items():
    if not os.path.exists(fpath): continue
    df = pd.read_csv(fpath)
    df["dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], errors="coerce")
    df = df.dropna(subset=["dt", "numero"]).sort_values(by="dt").reset_index(drop=True)
    nums = [str(x).strip() for x in df["numero"].tolist()]
    dates = df["fecha"].astype(str).tolist()
    
    streak = 0
    min_idx = max(lags) + rec_w + 2
    for i in range(min_idx, len(nums)):
        actual = nums[i]
        rec_set = set(nums[i-rec_w:i])
        raw_lags = [nums[i-l] for l in lags if i >= l]
        cands = sorted(list(set(raw_lags) - rec_set))
        d = dates[i]
        if start_date <= d <= end_date and streak in target_streaks and cands:
            counts_by_roulette[r_name] += 1
        if cands:
            streak = 0 if actual in cands else streak + 1

days = 47
print("Disparos y promedio diario por ruleta en el Sistema Nuevo (47 días):")
for r, cnt in sorted(counts_by_roulette.items(), key=lambda x: x[1], reverse=True):
    print(f"  {r:<25}: {cnt:>4} disparos | {cnt/days:.2f} disparos/día")
