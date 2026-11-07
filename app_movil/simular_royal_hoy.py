import pandas as pd

# Simular sorteo a sorteo hoy en Ruleta Royal
fpath = r"C:\Users\victo\nuevas_ruletas\data_vz\ruleta_royal_2anios.csv"
df = pd.read_csv(fpath)
df['num_str'] = df['numero'].astype(str).str.strip().str.lstrip("0").replace("", "0")
df['fecha_str'] = df['fecha'].astype(str)

lags = [19, 16, 31]
target_streaks = [1]
use_anti = True
blacklist = {"00"}

# Encontrar dónde empieza hoy
idx_hoy = df[df['fecha_str'] == '2026-11-02'].index.tolist()
start_idx = idx_hoy[0]

# Calcular racha hasta antes de hoy
streak = 0
cur_d = None
seen_today = set()
prev_was_repeat = False

for i in range(max(lags) + 7, start_idx):
    d = df.loc[i, 'fecha_str']
    act = df.loc[i, 'num_str']
    if d != cur_d:
        cur_d = d
        seen_today = set()
        prev_was_repeat = False
        
    rec = set(df.loc[i-6:i-1, 'num_str'])
    raw = [df.loc[i-l, 'num_str'] for l in lags]
    c_lag = sorted(list((set(raw) - rec) - blacklist))
    
    skip_anti = bool(use_anti and prev_was_repeat)
    if c_lag and not skip_anti:
        hit = (act in c_lag)
        streak = 0 if hit else streak + 1
    elif c_lag and skip_anti:
        hit = (act in c_lag)
        streak = 0 if hit else streak + 1
        
    is_rep = (act in seen_today)
    seen_today.add(act)
    prev_was_repeat = is_rep

print(f"Racha de Ruleta Royal al inicio de hoy: {streak}")

# Ahora procesar los sorteos de hoy
for i in idx_hoy:
    act = df.loc[i, 'num_str']
    hora = df.loc[i, 'hora']
    anim = df.loc[i, 'animal']
    rec = set(df.loc[i-6:i-1, 'num_str'])
    raw = [df.loc[i-l, 'num_str'] for l in lags]
    c_lag = sorted(list((set(raw) - rec) - blacklist))
    
    # Comprobar si tocaba apostar
    skip_anti = bool(use_anti and prev_was_repeat)
    apuesta = (streak in target_streaks) and (not skip_anti)
    
    hit = (act in c_lag)
    print(f"[{hora}] Racha previa: {streak} | Apostar: {apuesta} | Cands: {c_lag} | Salió: #{act} {anim} | Hit: {hit}")
    
    if c_lag:
        streak = 0 if hit else streak + 1
    is_rep = (act in seen_today)
    seen_today.add(act)
    prev_was_repeat = is_rep
