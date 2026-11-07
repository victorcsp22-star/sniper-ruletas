import json
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

state_path = 'C:/Users/victo/nuevas_ruletas/state_nuevas_ruletas.json'
with open(state_path, 'r', encoding='utf-8') as f:
    st = json.load(f)

print("=" * 60)
print("ESTADO ACTUAL DE BOT NUEVAS RULETAS (PC)")
print("=" * 60)
print("Última actualización:", st.get('last_updated'))
print("Bankroll:", st.get('bankroll'))
print("\nÚLTIMOS SORTEOS PROCESADOS POR RULETA:")
for k, v in st.get('last_processed_draw', {}).items():
    print(f"  {k:30}: {v}")

print("\nRACHAS Y FALLOS ACUMULADOS:")
streaks = st.get('streaks', {})
trig_miss = st.get('trigger_misses', {})
for k in sorted(streaks.keys()):
    print(f"  {k:30}: Racha={streaks[k]} | Trigger Misses={trig_miss.get(k, 0)}")

print("\nAPUESTAS PENDIENTES:")
pb = st.get('pending_bets', {})
if not pb:
    print("  (Ninguna apuesta pendiente actualmente)")
for k, v in pb.items():
    print(f"  {k}: {v}")
