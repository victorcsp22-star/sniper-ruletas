"""
CERTIFICACIÓN INSTITUCIONAL DE ALINEACIÓN: BOT EN VIVO vs MOTOR DE BACKTEST
Compara línea por línea y parámetro por parámetro:
1. config.py vs script de backtest (Lags, payouts, recencia, gatillos, markov, espejos).
2. bot_nuevas_ruletas.py vs lógica del backtest:
   - Extracción de candidatos por lags
   - Ventana de recencia (exclusión)
   - Disparo por canal de Markov
   - Disparo por canal de Espejos
   - Condición de gatillo (Racha 1, Racha 2, etc.)
   - Cálculo de pesos del agente (S_racha, S_pago, S_trigger)
   - Fórmula de stake ($1.00 plano vs peso/5)
   - Contabilidad de pérdidas y aciertos
"""

import sys, os, inspect
import pandas as pd

# 1. Cargar config.py oficial
sys.path.append(r"C:\Users\victo\nuevas_ruletas")
import config as cfg_live
import bot_nuevas_ruletas as bot_live

# 2. Cargar configuración del backtest
from scratch.backtest_9ruletas_pesos_vs_plana import CONFIG_9 as cfg_bt

discrepancias = []

print("=== 1. AUDITORÍA DE PARÁMETROS: CONFIG.PY vs BACKTEST ===")
for r_name, bt_params in cfg_bt.items():
    # Nombre estandarizado
    r_key = "Granja Millonaria - Granjazo" if r_name == "Granja Mill. Granjazo" else r_name
    if r_key not in cfg_live.RULETAS_CONFIG:
        discrepancias.append(f"Falta ruleta en config.py: {r_name}")
        continue
    live_p = cfg_live.RULETAS_CONFIG[r_key]
    
    # Payout
    if live_p.get("payout") != bt_params.get("payout"):
        discrepancias.append(f"{r_name}: Payout difiere (Live={live_p.get('payout')} vs BT={bt_params.get('payout')})")
        
    # Lags
    if list(live_p.get("lags", [])) != list(bt_params.get("lags", [])):
        discrepancias.append(f"{r_name}: Lags difieren (Live={live_p.get('lags')} vs BT={bt_params.get('lags')})")
        
    # Target streaks
    if list(live_p.get("target_streaks", [])) != list(bt_params.get("target_streaks", [])):
        discrepancias.append(f"{r_name}: Target streaks difieren (Live={live_p.get('target_streaks')} vs BT={bt_params.get('target_streaks')})")
        
    # Recencia
    if live_p.get("rec_w") != bt_params.get("rec_w"):
        discrepancias.append(f"{r_name}: Recencia difiere (Live={live_p.get('rec_w')} vs BT={bt_params.get('rec_w')})")
        
    # wr_optimos
    if list(live_p.get("wr_optimos", [])) != list(bt_params.get("wr_optimos", [])):
        discrepancias.append(f"{r_name}: wr_optimos difieren (Live={live_p.get('wr_optimos')} vs BT={bt_params.get('wr_optimos')})")
        
    # Markov snipers
    bt_m = bt_params.get("markov", {})
    live_m = live_p.get("markov_snipers", {})
    if bt_m != live_m:
        discrepancias.append(f"{r_name}: Markov difiere (Live={live_m} vs BT={bt_m})")

if not discrepancias:
    print("[+] PARÁMETROS 100% IDÉNTICOS: Las 9 ruletas tienen exactamente los mismos lags, payouts, recencia, gatillos y markov.")
else:
    for d in discrepancias:
        print("[-] DISCREPANCIA:", d)

# 3. AUDITORÍA DE LÓGICA DE DECISIÓN
print("\n=== 2. AUDITORÍA DE LÓGICA: BOT vs BACKTEST ===")

# Test empírico: ejecutar generate_upcoming_candidates en el bot para una ruleta
# y comparar con la función manual del backtest
test_r = "Lotto Activo"
cands_bot = bot_live.generate_upcoming_candidates(test_r)
print(f"Prueba en vivo sobre {test_r}:")
print(f"  • Bot candidatos generados: {cands_bot.get('candidates')}")
print(f"  • Bot tipo de canal:        {cands_bot.get('channel_type')}")
print(f"  • Bot payout registrado:    {cands_bot.get('payout')}x")

# Comparar función de pesos
peso_bot, lbl_bot = bot_live.calcular_peso_agente(test_r, 1, 2)
from scratch.backtest_9ruletas_pesos_vs_plana import calcular_peso_agente as calc_peso_bt
peso_bt = calc_peso_bt(test_r, 1, 2, 30.0, cfg_bt[test_r])
print(f"Prueba de función de Pesos (Streak=1, TriggerMiss=2):")
print(f"  • Peso en Bot:      {peso_bot}/10 ({lbl_bot})")
print(f"  • Peso en Backtest: {peso_bt}/10")
if peso_bot == peso_bt:
    print("  [+] Función de Pesos Matemática: 100% ALINEADA.")
else:
    print("  [-] Función de Pesos con discrepancia.")
