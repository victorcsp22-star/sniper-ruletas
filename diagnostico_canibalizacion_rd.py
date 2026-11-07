import os
import sys
import pandas as pd
import numpy as np

sys.path.append(r"C:\Users\victo\nuevas_ruletas")
from config import RULETAS_CONFIG
from backtest_cartera_8ruletas_general import extract_events_portfolio, run_portfolio_simulation

def diagnose():
    cfg_7 = {k: v for k, v in RULETAS_CONFIG.items() if v.get('active', True) and k != 'Lotto Activo RD Int'}
    cfg_8 = {k: v for k, v in RULETAS_CONFIG.items() if v.get('active', True)}
    
    events_7 = extract_events_portfolio(cfg_7)
    events_8 = extract_events_portfolio(cfg_8)
    
    print("=" * 80)
    print("DIAGNÓSTICO FORENSE: ¿POR QUÉ EMPEORA LA CARTERA AL INCORPORAR RD?")
    print("=" * 80)
    
    # 1. Rango temporal de eventos
    print(f"\n1. DESALINEACIÓN TEMPORAL DE LOS DATASETS:")
    print(f"  Cartera 7 fecha inicio: {events_7[0]['fecha']} ({events_7[0]['ruleta']}) | Fin: {events_7[-1]['fecha']}")
    print(f"  Cartera 8 fecha inicio: {events_8[0]['fecha']} ({events_8[0]['ruleta']}) | Fin: {events_8[-1]['fecha']}")
    
    # Eventos de RD antes de que existan las 7 ruletas (2022 a 2024)
    start_c7 = events_7[0]['dt']
    rd_solo = [e for e in events_8 if e['dt'] < start_c7]
    print(f"  Eventos de RD en solitario (antes del 2024-09-23): {len(rd_solo)} disparos (¡más de 2 años operando sola!)")
    
    # 2. Análisis del Circuit Breaker en la ventana común (2024 a 2026)
    events_8_common = [e for e in events_8 if e['dt'] >= start_c7]
    
    res_7 = run_portfolio_simulation(events_7, initial_bankroll=200.0)
    res_8 = run_portfolio_simulation(events_8_common, initial_bankroll=200.0)
    
    df_w7 = res_7["df_weeks"]
    df_w8 = res_8["df_weeks"]
    
    cb_7 = df_w7["cb_hit"].sum()
    cb_8 = df_w8["cb_hit"].sum()
    
    print(f"\n2. IMPACTO EN EL CIRCUIT BREAKER SEMANAL (Ventana común de 108 semanas):")
    print(f"  Semanas con Circuit Breaker en Cartera 7: {cb_7} semanas")
    print(f"  Semanas con Circuit Breaker en Cartera 8: {cb_8} semanas (Incremento: +{cb_8 - cb_7})")
    
    # 3. Disparos ganadores anulados por el Circuit Breaker
    # Vamos a simular semana a semana y ver qué disparos de Gatazo o Guacharo cayeron después del CB
    start_dt = events_8_common[0]["dt"]
    for ev in events_8_common:
        ev["week_idx"] = int((ev["dt"] - start_dt).total_seconds() // (7 * 86400))
        
    weeks_dict_8 = {}
    for ev in events_8_common:
        w = ev["week_idx"]
        if w not in weeks_dict_8: weeks_dict_8[w] = []
        weeks_dict_8[w].append(ev)
        
    missed_wins = []
    for w in range(len(df_w8)):
        row_w = df_w8.iloc[w]
        if row_w["cb_hit"]:
            evs = weeks_dict_8.get(w, [])
            b_start = row_w["b_start"]
            pnl_w = 0.0
            cb_tripped_at = None
            for idx_ev, ev in enumerate(evs):
                if pnl_w <= -b_start * 0.15:
                    # El CB se activó aquí. Todo lo posterior fue bloqueado
                    if ev["hit"]:
                        missed_wins.append({
                            "week": w + 1,
                            "ruleta": ev["ruleta"],
                            "dt": ev["dt"],
                            "payout": ev["payout"],
                            "pnl_bloqueado": ev["payout"] - ev["cost_units"]
                        })
                else:
                    cost = ev["cost_units"]
                    cob = ev["payout"] if ev["hit"] else 0.0
                    pnl_w += (cob - cost)

    df_missed = pd.DataFrame(missed_wins)
    print(f"\n3. CANIBALIZACIÓN DE ACIERTOS POR EL CIRCUIT BREAKER:")
    print(f"  Total disparos GANADORES de otras ruletas que fueron BLOQUEADOS porque RD activó el Circuit Breaker antes:")
    print(f"  {len(df_missed)} aciertos perdidos!")
    if len(df_missed) > 0:
        print("  Detalle de aciertos de alto pago bloqueados:")
        print(df_missed["ruleta"].value_counts())
        
    # 4. Desempeño de RD en los diferentes años (2022, 2023, 2024, 2025, 2026)
    df_rd = pd.DataFrame([e for e in events_8 if e['ruleta'] == 'Lotto Activo RD Int'])
    df_rd["year"] = pd.to_datetime(df_rd["fecha"]).dt.year
    print(f"\n4. CONSISTENCIA TEMPORAL DE RD POR AÑO:")
    for yr, grp in df_rd.groupby("year"):
        w = grp["hit"].sum()
        tot = len(grp)
        wr = w / tot * 100 if tot > 0 else 0
        pnl = w * 29 - (tot - w)
        print(f"  Año {yr}: Disparos={tot:>3} | Aciertos={w:>2} | Win Rate={wr:.2f}% | PnL Plano={pnl:+>4} u")

if __name__ == "__main__":
    diagnose()
