import os
import sys
import pandas as pd
import numpy as np
from datetime import timedelta

sys.path.append(r"C:\Users\victo\nuevas_ruletas")
from config import RULETAS_CONFIG

# Let's import the event extractor we tested
from test_event_extractor import extract_roulette_events

all_events = []
for r_name, cfg in RULETAS_CONFIG.items():
    if not cfg.get("active", False):
        continue
    evs = extract_roulette_events(r_name, cfg)
    all_events.extend(evs)

all_events.sort(key=lambda x: x["dt"])
print(f"Total eventos ordenados cronológicamente: {len(all_events):,}")
print(f"Primer evento: {all_events[0]['dt']} ({all_events[0]['ruleta']})")
print(f"Último evento: {all_events[-1]['dt']} ({all_events[-1]['ruleta']})")

# Let's check how many ruletas are active over time
dates_check = ["2024-11-01", "2025-05-01", "2026-02-01", "2026-05-01", "2026-10-01"]
for dc in dates_check:
    dt_c = pd.to_datetime(dc)
    # Check which ruletas have had events in the last 30 days
    active_in_30d = set()
    for ev in all_events:
        if dt_c - timedelta(days=30) <= ev["dt"] <= dt_c:
            active_in_30d.add(ev["ruleta"])
    print(f"Fecha: {dc} | Ruletas activas en últimos 30d: {len(active_in_30d)} -> {sorted(list(active_in_30d))}")
