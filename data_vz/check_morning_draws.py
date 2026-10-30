import datetime
import os
import sys
import pandas as pd
from sniper_bot import RULETAS_CONFIG as VZLA_CFG, evaluate_roulette_state as eval_vzla
from sniper_bot_brasil import RULETAS_CONFIG as BR_CFG, evaluate_roulette_state as eval_br

print("=== VERIFICACIÓN SORTEOS DE HOY 15-OCT-2026 (8:00 AM) ===")

for name, cfg in VZLA_CFG.items():
    if not cfg.get("active", True): continue
    df = pd.read_csv(cfg["file"], dtype={"numero": str})
    today = df[df["fecha"] == "2026-10-15"]
    print(f"\n{cfg['emoji']} {name}: {len(today)} sorteos hoy")
    for _, r in today.iterrows():
        print(f"   {r['hora']} -> Nº {r['numero']} ({r['animal']})")
    st = eval_vzla(name, df)
    print(f"   Racha actual: {st['racha_actual']} | Gatillo activo: {st['gatillo_activo']} | Candidatos próx: {st.get('candidatos', [])}")

for name, cfg in BR_CFG.items():
    df = pd.read_csv(cfg["file"], dtype={"numero": str})
    today = df[df["fecha"] == "2026-10-15"]
    print(f"\n{cfg['emoji']} {name}: {len(today)} sorteos hoy")
    for _, r in today.iterrows():
        print(f"   {r['hora']} -> Nº {r['numero']} ({r['animal']})")
    st = eval_br(name, df)
    print(f"   Racha actual: {st['racha_actual']} | Gatillo activo: {st['gatillo_activo']} | Candidatos próx: {st.get('candidatos', [])}")
