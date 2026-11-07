import os, glob, pandas as pd, collections

CONFIG_ANTERIOR = {
    "Lotto Activo": (r"C:\Users\victo\nuevas_ruletas\data_vz\lotto_activo_2anios.csv", [20, 18, 14], [1], 6),
    "La Granjita": (r"C:\Users\victo\nuevas_ruletas\data_vz\la_granjita_2anios.csv", [15, 17], [1], 9),
    "Ruleta Royal": (r"C:\Users\victo\nuevas_ruletas\data_vz\ruleta_royal_2anios.csv", [16, 19, 31], [1], 6),
    "Guacharo Activo": (r"C:\Users\victo\nuevas_ruletas\data_vz\guacharo_activo_2anios.csv", [31, 41, 25, 42, 35], [1], 8),
    "Gatazo": (r"C:\Users\victo\nuevas_ruletas\gatazo.csv", [35, 9, 20], [1, 2], 6),
    "Mega Animal 40": (r"C:\Users\victo\nuevas_ruletas\mega_animal_40.csv", [18, 21, 20], [1], 8),
    "Monje Millonario": (r"C:\Users\victo\nuevas_ruletas\monje_millonario.csv", [24, 42], [1], 6),
}

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

# Evaluar en el período donde todas las ruletas coexisten (los últimos 45 días: Sept 15 a Oct 31, 2026)
def count_triggers_in_period(cfg_dict, start_date="2026-09-15", end_date="2026-10-31"):
    daily_counts = collections.defaultdict(int)
    for r_name, (fpath, lags, target_streaks, rec_w) in cfg_dict.items():
        if not os.path.exists(fpath): continue
        df = pd.read_csv(fpath)
        df["dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], errors="coerce")
        df = df.dropna(subset=["dt", "numero"]).sort_values(by="dt").reset_index(drop=True)
        nums = [str(x).strip() for x in df["numero"].tolist()]
        dates = df["fecha"].astype(str).tolist()
        
        streak = 0
        min_idx = max(lags) + rec_w + 2
        for i in range(min_idx, len(nums)):
            d = dates[i]
            if d < start_date or d > end_date:
                # actualizar racha igualmente
                actual = nums[i]
                rec_set = set(nums[i-rec_w:i])
                raw_lags = [nums[i-l] for l in lags if i >= l]
                cands = sorted(list(set(raw_lags) - rec_set))
                if cands:
                    streak = 0 if actual in cands else streak + 1
                continue
            
            actual = nums[i]
            rec_set = set(nums[i-rec_w:i])
            raw_lags = [nums[i-l] for l in lags if i >= l]
            cands = sorted(list(set(raw_lags) - rec_set))
            
            if streak in target_streaks and cands:
                daily_counts[d] += 1
                
            if cands:
                streak = 0 if actual in cands else streak + 1
                
    return daily_counts

d_ant = count_triggers_in_period(CONFIG_ANTERIOR)
d_nue = count_triggers_in_period(CONFIG_NUEVA)

days = sorted(set(list(d_ant.keys()) + list(d_nue.keys())))
total_days = len(days)

tot_ant = sum(d_ant.values())
tot_nue = sum(d_nue.values())

avg_ant = tot_ant / total_days if total_days > 0 else 0
avg_nue = tot_nue / total_days if total_days > 0 else 0

print(f"Período evaluado: 15-Septiembre a 31-Octubre 2026 ({total_days} días)")
print(f"Sistema Anterior (7 Ruletas): {tot_ant} disparos | Promedio: {avg_ant:.2f} disparos/día")
print(f"Sistema Nuevo (9 Ruletas Élite): {tot_nue} disparos | Promedio: {avg_nue:.2f} disparos/día")
print(f"Diferencia: +{avg_nue - avg_ant:.2f} disparos/día (+{((avg_nue-avg_ant)/avg_ant)*100:.1f}%)")
