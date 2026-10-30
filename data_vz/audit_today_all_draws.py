import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd

lotteries = {
    "Lotto Activo": ("lotto_activo_2anios.csv", [20, 18, 14]),
    "La Granjita": ("la_granjita_2anios.csv", [15, 17]),
    "Ruleta Royal": ("ruleta_royal_2anios.csv", [16, 19, 31]),
    "Guacharo Activo": ("guacharo_activo_2anios.csv", [31, 41, 25, 42, 35]),
    "Selva Plus": ("selva_plus_2anios.csv", [35, 18, 36]),
    "Lotto Brasil": ("lottobrasil_2anios.csv", [12, 13, 24, 25]),
    "Lotto Bicho": ("lottobicho_2anios.csv", [12, 25, 13, 26]),
}

for name, (csv_f, lags) in lotteries.items():
    df = pd.read_csv(csv_f, dtype={"numero": str})
    today_df = df[df["fecha"] == "2026-10-14"]
    nums = df["numero"].astype(str).str.strip().tolist()
    
    # Calculate streak up to today start
    start_today = today_df.index[0] if not today_df.empty else len(df)
    streak = 0
    for i in range(max(lags) + 6, start_today):
        act = nums[i]
        rec6 = set(nums[i-6:i])
        cands = list(set([nums[i-l] for l in lags]) - rec6)
        hit = (act in cands)
        streak = 0 if hit else (streak + 1)
        
    print(f"\n=== {name.upper()} HOY (2026-10-14) | Racha al inicio del día: {streak} ===")
    for idx in today_df.index:
        row = df.iloc[idx]
        act = nums[idx]
        rec6 = set(nums[idx-6:idx])
        cands = list(set([nums[idx-l] for l in lags]) - rec6)
        hit = (act in cands)
        is_bet = (streak == 1 and len(cands) > 0)
        
        status = "🚨 DISPARO APUESTA REAL JUGADA" if is_bet else f"⏳ En espera (Racha={streak})"
        hit_txt = "✅ ACERTÓ" if hit else "❌ Falló"
        print(f"  {row['hora']:>8} -> Nº {act:>2} ({row['animal']:<10}) | Cands: {cands} | {hit_txt} | {status}")
        streak = 0 if hit else (streak + 1)
