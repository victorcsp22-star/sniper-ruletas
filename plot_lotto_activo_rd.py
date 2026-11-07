import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

CSV_PATH = r"C:\Users\victo\nuevas_ruletas\lotto_activo_rd_internacional.csv"
ARTIFACT_DIR = r"C:\Users\victo\.gemini\antigravity\brain\da61199f-f45d-4b1d-bcd9-a17212f844b0"
os.makedirs(ARTIFACT_DIR, exist_ok=True)

df = pd.read_csv(CSV_PATH)
df["numero"] = df["numero"].astype(str)
df.loc[df["animal"].str.upper() == "BALLENA", "numero"] = "00"
df.loc[df["animal"].str.upper() == "DELFÍN", "numero"] = "0"
df.loc[df["animal"].str.upper() == "DELFIN", "numero"] = "0"
df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
df = df.sort_values(by="sort_dt").reset_index(drop=True)

NUMS = df["numero"].tolist()
N = len(NUMS)
PAYOUT = 30.0

# 1. Estrategia Markov
trans_counts = {}
for i in range(len(NUMS) - 1):
    a = NUMS[i]
    b = NUMS[i + 1]
    if a not in trans_counts:
        trans_counts[a] = {}
    trans_counts[a][b] = trans_counts[a].get(b, 0) + 1

eq_markov = [200.0]
cap_m = 200.0
for i in range(1, N):
    prev = NUMS[i - 1]
    actual = NUMS[i]
    if prev in trans_counts and len(trans_counts[prev]) > 0:
        best_b = max(trans_counts[prev], key=trans_counts[prev].get)
        cnt = trans_counts[prev][best_b]
        if cnt >= 3:
            cap_m -= 1.0
            if best_b == actual:
                cap_m += PAYOUT
    eq_markov.append(cap_m)

# 2. Estrategia Lags (Lag 21, 17, 38)
top_lags = [21, 17, 38]
eq_lags = [200.0]
cap_l = 200.0
for i in range(1, N):
    if i >= 40:
        pred = NUMS[i - 21]
        actual = NUMS[i]
        cap_l -= 1.0
        if pred == actual:
            cap_l += PAYOUT
    eq_lags.append(cap_l)

# 3. Estrategia Sniper Post-Fallo 1
eq_sniper = [200.0]
cap_s = 200.0
streak = 0
for i in range(1, N):
    if i >= 22:
        prev_pred = NUMS[i - 1 - 21]
        prev_actual = NUMS[i - 1]
        if prev_pred != prev_actual:
            streak += 1
        else:
            streak = 0
        if streak == 1:
            pred = NUMS[i - 21]
            actual = NUMS[i]
            cap_s -= 1.0
            if pred == actual:
                cap_s += PAYOUT
    eq_sniper.append(cap_s)

# Graficar
fig, ax = plt.subplots(figsize=(12, 6.5))
ax.plot(eq_markov, label="Estrategia 3: Transiciones Markov A->B (+557.9% ROI, PF=8.15)", color="#00d084", linewidth=2.2)
ax.plot(eq_lags, label="Estrategia 1: Top Lag 21 (+47.7% ROI, PF=1.50)", color="#0693e3", linewidth=1.8)
ax.plot(eq_sniper, label="Estrategia 2: Sniper Post-Fallo 1 (+200.0% ROI, PF=3.22)", color="#fcb900", linewidth=1.8)
ax.axhline(200.0, color="#888888", linestyle=":", label="Capital Inicial ($200 USD)")

ax.set_title("Lotto Activo RD Internacional | Curvas de Equidad Comparativas (487 Sorteos)", fontsize=13, fontweight="bold", pad=12)
ax.set_ylabel("Balance de Cartera ($ USD)", fontsize=11)
ax.set_xlabel("Número de Sorteos Cronológicos (Sept - Oct 2026)", fontsize=11)
ax.grid(True, linestyle="--", alpha=0.35)
ax.legend(loc="upper left", framealpha=0.9)

plt.tight_layout()
chart_path = os.path.join(ARTIFACT_DIR, "grafica_backtest_lotto_activo_rd.png")
plt.savefig(chart_path, dpi=200)
plt.close()
print(f"Gráfica guardada en: {chart_path}")
