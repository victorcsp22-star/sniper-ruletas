import pandas as pd
import numpy as np
from scipy import stats

def check_lotto_rd():
    df = pd.read_csv('lotto_activo_rd_2anios.csv')
    nums = df['numero'].tolist()
    total = len(nums)
    p0 = 1.0 / 38
    be = 1.0 / 30 * 100
    print(f"Lotto Activo RD: {total} sorteos")
    for lag in range(7, 25):
        valid = total - lag
        matches = sum(1 for i in range(lag, total) if nums[i] == nums[i-lag])
        p_hat = matches / valid * 100
        z = (p_hat/100 - p0) / np.sqrt(p0*(1-p0)/valid)
        if p_hat > be:
            print(f"  Lag {lag}: {p_hat:.2f}% (Z: {z:+.2f})")

check_lotto_rd()
