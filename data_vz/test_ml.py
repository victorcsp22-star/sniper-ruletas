import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

def test_ml_predictability():
    df = pd.read_csv('lotto_activo_2anios.csv', encoding='utf-8-sig', dtype={'numero': str})
    df['sort_key'] = pd.to_datetime(df['fecha'] + ' ' + df['hora'], format='%Y-%m-%d %I:%M %p', errors='coerce')
    df = df.sort_values(by='sort_key').reset_index(drop=True)

    # Animals
    unique_numbers = sorted(df['numero'].unique().tolist())
    num_to_idx = {n: i for i, n in enumerate(unique_numbers)}
    df['target'] = df['numero'].map(num_to_idx)

    # Features:
    # 1. Target lag 1, 2, 3
    for lag in [1, 2, 3]:
        df[f'lag_{lag}'] = df['target'].shift(lag)

    # 2. Draw index of the day (1 to 12)
    df['draw_of_day'] = df.groupby('fecha').cumcount() + 1

    # 3. Hour and Day codes
    df['hour_code'] = pd.factorize(df['hora'])[0]
    df['day_code'] = pd.factorize(df['dia'])[0]

    # Drop early rows with NaN lags
    df_clean = df.dropna(subset=['lag_1', 'lag_2', 'lag_3']).copy()
    
    # Train / Test split: 70% Train, 30% Test (chronological walk-forward)
    split_idx = int(len(df_clean) * 0.70)
    train_df = df_clean.iloc[:split_idx]
    test_df = df_clean.iloc[split_idx:]

    feature_cols = ['lag_1', 'lag_2', 'lag_3', 'draw_of_day', 'hour_code', 'day_code']

    print(f"ML Test Split: Train = {len(train_df):,} sorteos, Test = {len(test_df):,} sorteos")
    
    # 1. Logistic Regression
    clf_lr = LogisticRegression(max_iter=500)
    clf_lr.fit(train_df[feature_cols], train_df['target'])
    preds_lr = clf_lr.predict(test_df[feature_cols])
    acc_lr = accuracy_score(test_df['target'], preds_lr)
    
    # 2. HistGradientBoosting
    clf_gb = HistGradientBoostingClassifier(max_iter=100, random_state=42)
    clf_gb.fit(train_df[feature_cols], train_df['target'])
    preds_gb = clf_gb.predict(test_df[feature_cols])
    acc_gb = accuracy_score(test_df['target'], preds_gb)

    # Baseline: Majority class in train
    maj_class = train_df['target'].mode()[0]
    acc_maj = accuracy_score(test_df['target'], [maj_class]*len(test_df))

    # Baseline: Pure random
    np.random.seed(42)
    rand_preds = np.random.randint(0, 38, size=len(test_df))
    acc_rand = accuracy_score(test_df['target'], rand_preds)

    print("\n--- RESULTADOS DE MODELOS PREDICTIVOS (TEST SET) ---")
    print(f"Azar puro (Teórico):          2.63%")
    print(f"Azar puro (Empírico):         {acc_rand*100:.2f}%")
    print(f"Clase mayoritaria (Top Hot):  {acc_maj*100:.2f}%")
    print(f"Regresión Logística:          {acc_lr*100:.2f}%")
    print(f"Gradient Boosting (GBDT):     {acc_gb*100:.2f}%")
    print(f"Umbral de Rentabilidad (BE):  3.33% (1/30)")
    
    # Calculate PnL for GBDT
    payout = 30.0
    pnl_gb = (acc_gb * len(test_df)) * payout - len(test_df)
    roi_gb = (pnl_gb / len(test_df)) * 100
    print(f"ROI del modelo Gradient Boosting: {roi_gb:+.2f}%")

if __name__ == "__main__":
    test_ml_predictability()
