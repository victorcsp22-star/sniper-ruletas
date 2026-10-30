import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd

df = pd.read_csv('ruleta_royal_2anios.csv')
today = df[df['fecha'] == '2026-10-14']
print("=== RULETA ROYAL HOY 2026-10-14 ===")
print(today[['fecha', 'hora', 'numero', 'animal']])

lags = [16, 19, 31]
nums = df['numero'].tolist()

yesterday = df[df['fecha'] == '2026-10-13']
all_idx = list(yesterday.index) + list(today.index)

start_idx = yesterday.index[0]
streak = 0
for i in range(max(lags) + 6, start_idx):
    act = nums[i]
    hist = nums[:i]
    rec6 = set(hist[-6:])
    cands = list(set([hist[-l] for l in lags]) - rec6)
    hit = (act in cands)
    if hit:
        streak = 0
    else:
        streak += 1

print(f"\nRacha al inicio de ayer (2026-10-13): {streak}")

for idx in all_idx:
    row = df.iloc[idx]
    act = nums[idx]
    hist = nums[:idx]
    rec6 = set(hist[-6:])
    cands_raw = [hist[-l] for l in lags]
    cands = list(set(cands_raw) - rec6)
    hit = (act in cands)
    gatillo_activo = (streak == 1)
    
    status_str = "DISPARO APUESTA REAL JUGADA" if (gatillo_activo and cands) else f"En espera (Racha previa: {streak})"
    print(f"[{row['fecha']} {row['hora']:>8}] Salió: {act:>2} ({row['animal']:<10}) | Cands: {cands} | Acierto: {str(hit):<5} | Racha antes: {streak:>2} -> {status_str}")
    
    if hit:
        streak = 0
    else:
        streak += 1
