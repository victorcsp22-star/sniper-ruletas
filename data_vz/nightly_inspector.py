"""
========================================================================================
 INSPECTOR NOCTURNO Y AUDITORÍA DE PRODUCCIÓN DIARIA (NIGHTLY INSPECTOR)
========================================================================================
Ejecuta la inspección diaria nocturna de ambos bots en paralelo:
 1. Bot Venezuela (5 Ruletas: Lotto Activo, Granjita, Royal, Guacharo, Selva Plus) - Capital: $1,000 USD
 2. Bot Brasil (2 Ruletas: Lotto Brasil, Lotto Bicho) - Capital: $200 USD

Genera y actualiza diariamente dos archivos Markdown dedicados e independientes:
 - diario_bot_venezuela.md
 - diario_bot_brasil.md

Incluye:
 - Auditoría punto a punto del último mes (desde 2026-09-14 hasta hoy 2026-10-14).
 - Estado táctico en vivo en tiempo real a la hora actual (con candidatos para el próximo sorteo).
========================================================================================
"""

import argparse
import datetime
import os
import sys
import pandas as pd

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACT_DIR = r"C:\Users\victo\.gemini\antigravity\brain\b416ad84-eb18-4af1-a597-d96da11175e8"

from live_production_tracker import (
    PORTFOLIOS_CONFIG,
    process_forward_production,
    get_health_multiplier
)

from sniper_bot import evaluate_roulette_state as eval_vzla, fetch_live_semana, load_and_sync_history as sync_vzla, RULETAS_CONFIG as CONFIG_VZLA
from sniper_bot_brasil import evaluate_roulette_state as eval_brasil, fetch_live_brasil, load_and_sync_history as sync_brasil, RULETAS_CONFIG as CONFIG_BRASIL


def build_markdown_bot_venezuela(res: dict, live_states: dict) -> str:
    df_d = res["df_daily"]
    df_l = res["df_ledger"]
    bankroll = res["final_bankroll"]
    peak = res["peak_capital"]
    initial = 1000.0
    net_pnl = bankroll - initial
    roi_pct = (net_pnl / initial * 100.0)
    dd_current = ((peak - bankroll) / peak * 100.0) if peak > 0 else 0.0

    tot_bets = int(df_d["total_disparos"].sum()) if not df_d.empty else 0
    tot_hits = int(df_d["aciertos"].sum()) if not df_d.empty else 0
    tot_invested = df_d["total_invertido"].sum() if not df_d.empty else 0.0
    tot_returned = df_d["total_retornado"].sum() if not df_d.empty else 0.0
    wr_global = (tot_hits / tot_bets * 100.0) if tot_bets > 0 else 0.0

    last_date = df_d["fecha"].iloc[-1] if not df_d.empty else "N/A"
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %I:%M %p')

    lines = []
    lines.append(f"# 🇻🇪 Diario de Producción: Bot Venezuela (5 Ruletas en Paralelo)")
    lines.append("")
    lines.append(f"> **Última Actualización:** {now_str}  ")
    lines.append(f"> **Período Auditado:** Último Mes Completo (14-Septiembre-2026 al 14-Octubre-2026 | 31 Días)  ")
    lines.append(f"> **Estrategia Operativa:** Gatillo Sniper Post-Fallo 1 | Filtro Recencia 6h | Full Kelly Modulado Grossman-Zhou (Floor 40%)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. Totales Acumulados del Bot (1 Mes de Producción)")
    lines.append("")
    lines.append("| Métrica Clave | Valor Actual | Comentarios de Control |")
    lines.append("| :--- | :---: | :--- |")
    lines.append(f"| **Capital Inicial** | **$1,000.00 USD** | Capital semilla de arranque hace 1 mes (14-Sep-2026) |")
    lines.append(f"| **Capital Actual** | **${bankroll:,.2f} USD** | Balance líquido auditado en cuenta hoy |")
    lines.append(f"| **Beneficio Neto (PnL)** | **{'+' if net_pnl>=0 else ''}${net_pnl:,.2f} USD** ({'+' if roi_pct>=0 else ''}{roi_pct:.2f}%) | Rendimiento neto en forward testing |")
    lines.append(f"| **Pico Histórico (ATH)** | **${peak:,.2f} USD** | Máximo capital alcanzado en el mes |")
    lines.append(f"| **Drawdown Actual** | **{dd_current:.2f}%** | Suelo de protección activo en ${peak*0.60:,.2f} USD (MDD máx 40%) |")
    lines.append(f"| **Total Disparos Sniper** | **{tot_bets:,} apuestas** | Solo ejecutadas cuando racha virtual es exactamente 1 |")
    lines.append(f"| **Total Aciertos** | **{tot_hits:,}** ({wr_global:.2f}% Win Rate) | Promedio ponderado de las 5 ruletas |")
    lines.append(f"| **Total Invertido** | **${tot_invested:,.2f} USD** | Volumen transaccional gestionado en 31 días |")
    lines.append(f"| **Total Cobrado** | **${tot_returned:,.2f} USD** | Retornos brutos de apuestas ganadoras |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 2. Histórico de Producción Diaria (Punto a Punto: 1 Mes Completo)")
    lines.append("")
    lines.append("| Fecha | Balance Inicial | Balance Cierre | PnL Diario ($) | PnL Diario (%) | Disparos | Aciertos (WR%) | Invertido | Cobrado | Drawdown |")
    lines.append("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

    for _, row in df_d.iterrows():
        sign = "+" if row["pnl_neto"] >= 0 else ""
        lines.append(f"| {row['fecha']} | ${row['balance_inicial']:,.2f} | ${row['balance_final']:,.2f} | **{sign}${row['pnl_neto']:,.2f}** | {sign}{row['pnl_pct']:.2f}% | {int(row['total_disparos'])} | {int(row['aciertos'])} ({row['win_rate']:.1f}%) | ${row['total_invertido']:,.2f} | ${row['total_retornado']:,.2f} | {row['drawdown_actual']:.2f}% |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 3. Estado Táctico y Agente de Salud por Ruleta al Cierre del Día")
    lines.append("")
    lines.append("| Ruleta | Lags Activos | Payout | Racha Fallos | WR Reciente (50s) | Break-Even | Salud Edge | Diagnóstico Salud | Ponderación |")
    lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: |")

    vz_meta = PORTFOLIOS_CONFIG["venezuela"]["ruletas"]
    for r_name, r_cfg in vz_meta.items():
        s = res["streaks"].get(r_name, 0)
        hist = res["signals_hist"].get(r_name, [])
        bw = res["base_wrs"].get(r_name, 10.0)
        hw, hw_label, hscore = get_health_multiplier(hist, bw, r_cfg["be_rate"])
        rec_hits = sum(hist[-50:]) if hist else 0
        rec_len = len(hist[-50:]) if hist else 0
        rec_wr = (rec_hits / rec_len * 100.0) if rec_len > 0 else 0.0
        status = "🟢 Salud Óptima" if hscore >= 100 else ("🟡 Normal" if rec_wr >= r_cfg["be_rate"] else "🔴 Degradada")
        lags_str = str(r_cfg["lags"])
        lines.append(f"| {r_cfg['emoji']} **{r_name}** | `{lags_str}` | {r_cfg['payout']:.0f}x | **{s}** | {rec_wr:.1f}% ({rec_hits}/{rec_len}) | {r_cfg['be_rate']:.2f}% | **{hscore:.1f}%** | {status} | **{hw:.2f}x** |")

    lines.append("")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 4. Historial Visual de Sorteos Jugados (Auditoría Jugada por Jugada)")
    lines.append("")
    lines.append("> **Regla Operativa:** El bot solo arriesga capital cuando la racha virtual previa es exactamente 1 (`Gatillo Post-Fallo 1`). En cualquier otro estado se mantiene en observación disciplinada sin arriesgar saldo.")
    lines.append("")
    lines.append(f"**Total Disparos:** `{tot_bets}` | **Aciertos:** `{tot_hits}` ({wr_global:.2f}% Win Rate) | **Fallos:** `{tot_bets - tot_hits}`")
    lines.append("")
    lines.append("| Fecha | Hora | Ruleta | Animales Seleccionados | Resultado Ganador | Condición | Invertido ($) | Cobrado ($) | PnL Neto ($) | Balance Cuenta ($) |")
    lines.append("| :---: | :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |")

    if not df_l.empty:
        for _, row in df_l.iloc[::-1].iterrows():
            pnl_val = row["pnl"]
            sign = "+" if pnl_val >= 0 else ""
            cands_disp = row.get("animales_seleccionados", row.get("candidatos", ""))
            res_disp = row.get("resultado_sorteo", f"[{row.get('resultado_num','')}] {row.get('resultado_animal','')}")
            cond_disp = row.get("condicion", "🟢 GANADA" if row.get("acierto", 0) == 1 else "🔴 PERDIDA")
            inv = row.get("costo_total", 0.0)
            cob = row.get("payout_cobrado", 0.0)
            bal = row.get("balance_cierre", 0.0)
            lines.append(f"| {row['fecha']} | {row['hora']} | {row['ruleta']} | `{cands_disp}` | **{res_disp}** | {cond_disp} | ${inv:,.2f} | ${cob:,.2f} | **{sign}${pnl_val:,.2f}** | ${bal:,.2f} |")
    else:
        lines.append("| - | - | - | Sin jugadas registradas | - | - | - | - | - | - |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"## 5. Estado Actual en Tiempo Real a esta Hora ({now_str})")
    lines.append("")
    for r_name, st in live_states.items():
        emoji = st.get("emoji", "🎲")
        lotto = st.get("lotto", r_name)
        streak = st.get("racha_actual", 0)
        gatillo = st.get("gatillo_activo", False)
        ult = st.get("ultimo_resultado", "N/A")
        cands = st.get("candidatos", [])
        
        lines.append(f"### {emoji} {lotto}")
        lines.append(f"- **Último Sorteo Sincronizado:** `{ult}`")
        lines.append(f"- **Racha Actual de Fallos:** `{streak}` sorteo(s)")
        if gatillo and cands:
            lines.append(f"- 🚨 **GATILLO ACTIVO:** ¡DISPARAR EN PRÓXIMO SORTEO!")
            lines.append(f"- **Candidatos a Jugar:** {', '.join(cands)}")
        else:
            lines.append(f"- ⏳ **Estado:** En Espera (Racha={streak}). No apostar.")
        lines.append("")

    lines.append("---")
    lines.append("*(Archivo actualizado automáticamente por `nightly_inspector.py` en cada inspección nocturna)*")
    
    return "\n".join(lines)


def build_markdown_bot_brasil(res: dict, live_states: dict) -> str:
    df_d = res["df_daily"]
    df_l = res["df_ledger"]
    bankroll = res["final_bankroll"]
    peak = res["peak_capital"]
    initial = 200.0
    net_pnl = bankroll - initial
    roi_pct = (net_pnl / initial * 100.0)
    dd_current = ((peak - bankroll) / peak * 100.0) if peak > 0 else 0.0

    tot_bets = int(df_d["total_disparos"].sum()) if not df_d.empty else 0
    tot_hits = int(df_d["aciertos"].sum()) if not df_d.empty else 0
    tot_invested = df_d["total_invertido"].sum() if not df_d.empty else 0.0
    tot_returned = df_d["total_retornado"].sum() if not df_d.empty else 0.0
    wr_global = (tot_hits / tot_bets * 100.0) if tot_bets > 0 else 0.0

    last_date = df_d["fecha"].iloc[-1] if not df_d.empty else "N/A"
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %I:%M %p')

    lines = []
    lines.append(f"# 🇧🇷 Diario de Producción: Bot Brasil (Lotto Brasil & Lotto Bicho)")
    lines.append("")
    lines.append(f"> **Última Actualización:** {now_str}  ")
    lines.append(f"> **Período Auditado:** Último Mes Completo (14-Septiembre-2026 al 14-Octubre-2026 | 31 Días)  ")
    lines.append(f"> **Estrategia Operativa:** Gatillo Sniper Post-Fallo 1 | Memoria Circadiana Lag 12 | Full Kelly Grossman-Zhou (Floor 40%)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. Totales Acumulados del Bot (1 Mes de Producción)")
    lines.append("")
    lines.append("| Métrica Clave | Valor Actual | Comentarios de Control |")
    lines.append("| :--- | :---: | :--- |")
    lines.append(f"| **Capital Inicial** | **$200.00 USD** | Capital semilla de arranque hace 1 mes (14-Sep-2026) |")
    lines.append(f"| **Capital Actual** | **${bankroll:,.2f} USD** | Balance líquido auditado en cuenta hoy |")
    lines.append(f"| **Beneficio Neto (PnL)** | **{'+' if net_pnl>=0 else ''}${net_pnl:,.2f} USD** ({'+' if roi_pct>=0 else ''}{roi_pct:.2f}%) | Rendimiento neto en forward testing |")
    lines.append(f"| **Pico Histórico (ATH)** | **${peak:,.2f} USD** | Máximo capital alcanzado en el mes |")
    lines.append(f"| **Drawdown Actual** | **{dd_current:.2f}%** | Suelo de protección activo en ${peak*0.60:,.2f} USD (MDD máx 40%) |")
    lines.append(f"| **Total Disparos Sniper** | **{tot_bets:,} apuestas** | Solo ejecutadas cuando racha virtual es exactamente 1 |")
    lines.append(f"| **Total Aciertos** | **{tot_hits:,}** ({wr_global:.2f}% Win Rate) | Promedio de las 2 ruletas brasileñas |")
    lines.append(f"| **Total Invertido** | **${tot_invested:,.2f} USD** | Volumen transaccional gestionado en 31 días |")
    lines.append(f"| **Total Cobrado** | **${tot_returned:,.2f} USD** | Retornos brutos de apuestas ganadoras |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 2. Histórico de Producción Diaria (Punto a Punto: 1 Mes Completo)")
    lines.append("")
    lines.append("| Fecha | Balance Inicial | Balance Cierre | PnL Diario ($) | PnL Diario (%) | Disparos | Aciertos (WR%) | Invertido | Cobrado | Drawdown |")
    lines.append("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

    for _, row in df_d.iterrows():
        sign = "+" if row["pnl_neto"] >= 0 else ""
        lines.append(f"| {row['fecha']} | ${row['balance_inicial']:,.2f} | ${row['balance_final']:,.2f} | **{sign}${row['pnl_neto']:,.2f}** | {sign}{row['pnl_pct']:.2f}% | {int(row['total_disparos'])} | {int(row['aciertos'])} ({row['win_rate']:.1f}%) | ${row['total_invertido']:,.2f} | ${row['total_retornado']:,.2f} | {row['drawdown_actual']:.2f}% |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 3. Estado del Agente de Salud por Ruleta al Cierre del Día")
    lines.append("")
    lines.append("| Ruleta | Lags Circadianos | Payout | Racha Fallos | WR Reciente (50s) | Break-Even | Salud Edge | Diagnóstico Salud | Ponderación |")
    lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: |")

    br_meta = PORTFOLIOS_CONFIG["brasil"]["ruletas"]
    for r_name, r_cfg in br_meta.items():
        s = res["streaks"].get(r_name, 0)
        hist = res["signals_hist"].get(r_name, [])
        bw = res["base_wrs"].get(r_name, 10.0)
        hw, hw_label, hscore = get_health_multiplier(hist, bw, r_cfg["be_rate"])
        rec_hits = sum(hist[-50:]) if hist else 0
        rec_len = len(hist[-50:]) if hist else 0
        rec_wr = (rec_hits / rec_len * 100.0) if rec_len > 0 else 0.0
        status = "🟢 Salud Óptima" if hscore >= 100 else ("🟡 Normal" if rec_wr >= r_cfg["be_rate"] else "🔴 Degradada")
        lags_str = str(r_cfg["lags"])
        lines.append(f"| {r_cfg['emoji']} **{r_name}** | `{lags_str}` | {r_cfg['payout']:.0f}x | **{s}** | {rec_wr:.1f}% ({rec_hits}/{rec_len}) | {r_cfg['be_rate']:.2f}% | **{hscore:.1f}%** | {status} | **{hw:.2f}x** |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 4. Historial Visual de Sorteos Jugados (Auditoría Jugada por Jugada)")
    lines.append("")
    lines.append("> **Regla Operativa:** El bot solo arriesga capital cuando la racha virtual previa es exactamente 1 (`Gatillo Post-Fallo 1`). En cualquier otro estado se mantiene en observación disciplinada sin arriesgar saldo.")
    lines.append("")
    lines.append(f"**Total Disparos:** `{tot_bets}` | **Aciertos:** `{tot_hits}` ({wr_global:.2f}% Win Rate) | **Fallos:** `{tot_bets - tot_hits}`")
    lines.append("")
    lines.append("| Fecha | Hora | Ruleta | Animales Seleccionados | Resultado Ganador | Condición | Invertido ($) | Cobrado ($) | PnL Neto ($) | Balance Cuenta ($) |")
    lines.append("| :---: | :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |")

    if not df_l.empty:
        for _, row in df_l.iloc[::-1].iterrows():
            pnl_val = row["pnl"]
            sign = "+" if pnl_val >= 0 else ""
            cands_disp = row.get("animales_seleccionados", row.get("candidatos", ""))
            res_disp = row.get("resultado_sorteo", f"[{row.get('resultado_num','')}] {row.get('resultado_animal','')}")
            cond_disp = row.get("condicion", "🟢 GANADA" if row.get("acierto", 0) == 1 else "🔴 PERDIDA")
            inv = row.get("costo_total", 0.0)
            cob = row.get("payout_cobrado", 0.0)
            bal = row.get("balance_cierre", 0.0)
            lines.append(f"| {row['fecha']} | {row['hora']} | {row['ruleta']} | `{cands_disp}` | **{res_disp}** | {cond_disp} | ${inv:,.2f} | ${cob:,.2f} | **{sign}${pnl_val:,.2f}** | ${bal:,.2f} |")
    else:
        lines.append("| - | - | - | Sin jugadas registradas | - | - | - | - | - | - |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"## 5. Estado Actual en Tiempo Real a esta Hora ({now_str})")
    lines.append("")
    for r_name, st in live_states.items():
        emoji = st.get("emoji", "🎲")
        lotto = st.get("lotto", r_name)
        streak = st.get("racha_actual", 0)
        gatillo = st.get("gatillo_activo", False)
        ult = st.get("ultimo_resultado", "N/A")
        cands = st.get("candidatos", [])
        
        lines.append(f"### {emoji} {lotto}")
        lines.append(f"- **Último Sorteo Sincronizado:** `{ult}`")
        lines.append(f"- **Racha Actual de Fallos:** `{streak}` sorteo(s)")
        if gatillo and cands:
            lines.append(f"- 🚨 **GATILLO ACTIVO:** ¡DISPARAR EN PRÓXIMO SORTEO!")
            lines.append(f"- **Candidatos a Jugar:** {', '.join(cands)}")
        else:
            lines.append(f"- ⏳ **Estado:** En Espera (Racha={streak}). No apostar.")
        lines.append("")

    lines.append("---")
    lines.append("*(Archivo actualizado automáticamente por `nightly_inspector.py` en cada inspección nocturna)*")

    return "\n".join(lines)


def run_inspection(start_date: str = "2026-09-14"):
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %I:%M %p')
    print("\n" + "=" * 95)
    print(f" 🌙 AUDITORÍA DE PRODUCCIÓN DIARIA (1 MES COMPLETO: {start_date} A HOY)")
    print(f"    Hora Actual de Inspección: {now_str}")
    print("=" * 95)

    # 1. Sincronizar sorteos en vivo primero
    print("\n[+] Sincronizando sorteos en vivo...")
    live_vz = fetch_live_semana()
    live_states_vz = {}
    for lotto in CONFIG_VZLA:
        df_s = sync_vzla(lotto, live_vz.get(lotto, []))
        st = eval_vzla(lotto, df_s)
        live_states_vz[lotto] = st

    live_br = fetch_live_brasil()
    live_states_br = {}
    for lotto in CONFIG_BRASIL:
        df_s = sync_brasil(lotto, live_br.get(lotto, []))
        st = eval_brasil(lotto, df_s)
        live_states_br[lotto] = st

    # 2. Procesar Portafolio Venezuela (Capital Inicial: $1,000 USD)
    print("\n[+] Auditando Bot Venezuela (5 Ruletas | Capital $1,000 USD)...")
    vzla_res = process_forward_production("venezuela", start_date=start_date)
    md_vzla = build_markdown_bot_venezuela(vzla_res, live_states_vz)

    file_vzla_local = os.path.join(BASE_DIR, "diario_bot_venezuela.md")
    file_vzla_art = os.path.join(ARTIFACT_DIR, "diario_bot_venezuela.md")
    with open(file_vzla_local, "w", encoding="utf-8") as f:
        f.write(md_vzla)
    with open(file_vzla_art, "w", encoding="utf-8") as f:
        f.write(md_vzla)
    print(f"    [✓] Guardado diario Venezuela (31 días) en: {file_vzla_local}")

    # 3. Procesar Portafolio Brasil (Capital Inicial: $200 USD)
    print("\n[+] Auditando Bot Brasil (2 Ruletas | Capital $200 USD)...")
    br_res = process_forward_production("brasil", start_date=start_date)
    md_br = build_markdown_bot_brasil(br_res, live_states_br)

    file_br_local = os.path.join(BASE_DIR, "diario_bot_brasil.md")
    file_br_art = os.path.join(ARTIFACT_DIR, "diario_bot_brasil.md")
    with open(file_br_local, "w", encoding="utf-8") as f:
        f.write(md_br)
    with open(file_br_art, "w", encoding="utf-8") as f:
        f.write(md_br)
    print(f"    [✓] Guardado diario Brasil (31 días) en: {file_br_local}")

    # 4. Mostrar Resumen Ejecutivo en Pantalla
    print("\n" + "=" * 95)
    print(" 📋 RESUMEN CONSOLIDADO DE LA INSPECCIÓN (1 MES COMPLETO)")
    print("=" * 95)
    print(f" {'Portafolio':<28} | {'Capital Inicial':<16} | {'Capital Cierre':<16} | {'PnL Total':<18} | {'Drawdown Actual'}")
    print("-" * 95)
    
    vz_pnl = vzla_res['final_bankroll'] - 1000.0
    vz_pnl_str = f"{'+' if vz_pnl>=0 else ''}${vz_pnl:,.2f} ({(vz_pnl/1000*100):+.1f}%)"
    vz_dd = ((vzla_res['peak_capital'] - vzla_res['final_bankroll']) / vzla_res['peak_capital'] * 100.0) if vzla_res['peak_capital'] > 0 else 0.0
    print(f" 🇻🇪 Bot Venezuela (5 Ruletas)   | $1,000.00 USD    | ${vzla_res['final_bankroll']:,.2f} USD    | {vz_pnl_str:<18} | {vz_dd:.2f}%")

    br_pnl = br_res['final_bankroll'] - 200.0
    br_pnl_str = f"{'+' if br_pnl>=0 else ''}${br_pnl:,.2f} ({(br_pnl/200*100):+.1f}%)"
    br_dd = ((br_res['peak_capital'] - br_res['final_bankroll']) / br_res['peak_capital'] * 100.0) if br_res['peak_capital'] > 0 else 0.0
    print(f" 🇧🇷 Bot Brasil (2 Ruletas)      | $200.00 USD      | ${br_res['final_bankroll']:,.2f} USD    | {br_pnl_str:<18} | {br_dd:.2f}%")

    tot_cap = vzla_res['final_bankroll'] + br_res['final_bankroll']
    tot_pnl = vz_pnl + br_pnl
    tot_pnl_str = f"{'+' if tot_pnl>=0 else ''}${tot_pnl:,.2f} ({(tot_pnl/1200*100):+.1f}%)"
    print("-" * 95)
    print(f" 🌐 TOTAL CONSOLIDADO            | $1,200.00 USD    | ${tot_cap:,.2f} USD    | {tot_pnl_str:<18} | Max DD: {max(vz_dd, br_dd):.2f}%")
    print("=" * 95)

    print("\n" + "=" * 95)
    print(f" 🎯 ESTADO EN TIEMPO REAL A ESTA HORA ({now_str}) | PRÓXIMO SORTEO: 2:00 PM")
    print("=" * 95)
    print(" 🇻🇪 VENEZUELA:")
    for r_name, st in live_states_vz.items():
        emoji = st.get("emoji", "🎲")
        streak = st.get("racha_actual", 0)
        gatillo = st.get("gatillo_activo", False)
        ult = st.get("ultimo_resultado", "N/A")
        print(f"   {emoji} {r_name:<20}: Último -> {ult} | Racha: {streak} | {'🚨 ¡GATILLO ACTIVO!' if gatillo else '⏳ En Espera'}")
        if gatillo and st.get("candidatos"):
            print(f"       👉 Jugar ({len(st['candidatos'])} cands): {', '.join(st['candidatos'])}")

    print("\n 🇧🇷 BRASIL:")
    for r_name, st in live_states_br.items():
        emoji = st.get("emoji", "🎲")
        streak = st.get("racha_actual", 0)
        gatillo = st.get("gatillo_activo", False)
        ult = st.get("ultimo_resultado", "N/A")
        print(f"   {emoji} {r_name:<20}: Último -> {ult} | Racha: {streak} | {'🚨 ¡GATILLO ACTIVO!' if gatillo else '⏳ En Espera'}")
        if gatillo and st.get("candidatos"):
            print(f"       👉 Jugar ({len(st['candidatos'])} cands): {', '.join(st['candidatos'])}")
    print("=" * 95 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspector Nocturno Diario de Bots Sniper")
    parser.add_argument("--start_date", type=str, default="2026-09-14", help="Fecha de inicio (hace 1 mes: 2026-09-14)")
    args = parser.parse_args()
    run_inspection(start_date=args.start_date)
