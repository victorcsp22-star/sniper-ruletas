import datetime
import os
import sys
import pandas as pd
from sniper_bot import fetch_live_semana, load_and_sync_history, RULETAS_CONFIG
from sniper_bot_brasil import fetch_live_brasil, load_and_sync_history as load_and_sync_brasil, RULETAS_CONFIG as RULETAS_BRASIL

print("=== Sincronizando Venezuela desde TuAzar ===")
live_vz = fetch_live_semana()
for lotto in RULETAS_CONFIG:
    df_sync = load_and_sync_history(lotto, live_vz.get(lotto, []))
    last = df_sync.iloc[-1]
    print(f" {lotto}: {len(df_sync)} sorteos | Último: {last['fecha']} {last['hora']} -> {last['numero']} ({last['animal']})")

print("\n=== Sincronizando Brasil desde LottoBichos API ===")
live_br = fetch_live_brasil()
for lotto in RULETAS_BRASIL:
    df_sync = load_and_sync_brasil(lotto, live_br.get(lotto, []))
    last = df_sync.iloc[-1]
    print(f" {lotto}: {len(df_sync)} sorteos | Último: {last['fecha']} {last['hora']} -> {last['numero']} ({last['animal']})")
