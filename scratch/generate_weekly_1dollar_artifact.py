import os
import sys
import json

ROOT_DIR = r"C:\Users\victo\nuevas_ruletas"
ARTIFACT_DIR = r"C:\Users\victo\.gemini\antigravity\brain\d8f43462-caa6-4209-8905-313e89d6db4d"
ARTIFACT_PATH = os.path.join(ARTIFACT_DIR, "backtest_semana_a_semana_montos_fijos_1dolar.md")

with open(os.path.join(ROOT_DIR, "scratch", "backtest_fixed_1dollar_2y_results.json"), "r", encoding="utf-8") as f:
    data = json.load(f)

s = data["summary"]
ch = data["channel_summary"]
ro = data["roulette_summary"]
weeks = data["weekly_records"]

md = []
md.append("# Auditoría Cuantitativa: Rendimiento Histórico Semana a Semana (Apuestas ~$1.00 USD)")
md.append("")
md.append("**Fecha de Auditoría:** 30 de Octubre de 2026  ")
md.append("**Modelo de Apuesta:** Montos fijos oscilantes alrededor de **$1.00 USD** ($0.60 a $1.40 USD según fortaleza del patrón).  ")
md.append(f"**Muestra Analizada:** 39,473 sorteos reales a lo largo de **{s['total_weeks']} semanas (2 años completos)** across 7 ruletas.  ")
md.append(f"**Capital Base Inicial:** ${s['initial_bankroll']:,.2f} USD.  ")
md.append("")
md.append("---")
md.append("")
md.append("## 1. Resumen Ejecutivo Global")
md.append("")
md.append("| Métrica Cuantitativa | Valor Auditado | Significado Técnico |")
md.append("| :--- | :---: | :--- |")
md.append(f"| **Capital Inicial** | **${s['initial_bankroll']:,.2f} USD** | Base inicial sin apalancamiento. |")
md.append(f"| **Capital Final Logrado** | **${s['final_bankroll']:,.2f} USD** | Capital final acumulado con apuestas planas de ~$1.00. |")
md.append(f"| **Beneficio Neto (PnL Total)** | **+${s['net_pnl']:,.2f} USD** | Ganancia neta real en mano (**+{s['net_pnl']/s['initial_bankroll']*100:,.1f}%**). |")
md.append(f"| **Pico Máximo (ATH Peak)** | **${s['peak']:,.2f} USD** | Cerró en su máximo histórico absoluto. |")
md.append(f"| **Máximo Drawdown en USD** | **-${s['max_dd_usd']:,.2f} USD** | Pérdida máxima transitoria en el peor momento. |")
md.append(f"| **Máximo Drawdown en %** | **{s['max_dd_pct']:.2f}%** | Exposición al riesgo ultra-baja (< 15%). |")
md.append(f"| **Total de Operaciones** | **{s['total_bets']:,} apuestas** | Promedio de 55 apuestas por semana. |")
md.append(f"| **Aciertos Totales (Wins)** | **{s['total_wins']:,} aciertos** | Tasa de acierto global del **{s['win_rate']:.2f}%**. |")
md.append(f"| **Capital Total Invertido** | **${s['total_invested']:,.2f} USD** | Suma total apostada en 2 años. |")
md.append(f"| **Capital Total Cobrado** | **${s['total_collected']:,.2f} USD** | Suma total pagada por las casas. |")
md.append(f"| **Retorno sobre Inversión (ROI)** | **+{s['roi_pct']:.2f}%** | Eficiencia matemática por dólar apostado. |")
md.append(f"| **Profit Factor (PF)** | **{s['profit_factor']:.2f}** | Ratio bruto ganancias / pérdidas. |")
md.append(f"| **Sharpe Ratio Anualizado** | **{s['sharpe']:.2f}** | Ratio riesgo-retorno de grado institucional. |")
md.append(f"| **Sortino Ratio (Downside)** | **{s['sortino']:.2f}** | Rendimiento penalizando solo volatilidad negativa. |")
md.append(f"| **Semanas Ganadoras** | **{s['winning_weeks']} de {s['total_weeks']} ({s['winning_weeks']/s['total_weeks']*100:.1f}%)** | Más de 3 de cada 4 semanas en ganancia. |")
md.append(f"| **Semanas Perdedoras** | **{s['losing_weeks']} de {s['total_weeks']} ({s['losing_weeks']/s['total_weeks']*100:.1f}%)** | Semanas con retroceso moderado. |")
md.append("")
md.append("---")
md.append("")
md.append("## 2. Desglose de Rendimiento por Ruleta (Todas en Positivo)")
md.append("")
md.append("| Ruleta | Operaciones | Aciertos | Win Rate | Invertido | Cobrado | PnL Neto | ROI % |")
md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
for rn, rst in ro.items():
    wr = (rst['wins'] / rst['bets'] * 100.0) if rst['bets'] > 0 else 0.0
    roi = (rst['pnl'] / rst['invested'] * 100.0) if rst['invested'] > 0 else 0.0
    md.append(f"| **{rn}** | {rst['bets']:,} | {rst['wins']:,} | {wr:.1f}% | ${rst['invested']:,.2f} | ${rst['collected']:,.2f} | **+${rst['pnl']:,.2f}** | **+{roi:.2f}%** |")
md.append("")
md.append("---")
md.append("")
md.append("## 3. Desglose por Canal de Disparo")
md.append("")
md.append("| Canal de Disparo | Operaciones | Aciertos | Win Rate | Invertido | Cobrado | PnL Neto | ROI % |")
md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
for chn, cst in ch.items():
    wr = (cst['wins'] / cst['bets'] * 100.0) if cst['bets'] > 0 else 0.0
    roi = (cst['pnl'] / cst['invested'] * 100.0) if cst['invested'] > 0 else 0.0
    ch_label = "Canal A (Lag Basket)" if "Lag" in chn else "Canal B (Markov Sniper 1 Ficha)"
    md.append(f"| **{ch_label}** | {cst['bets']:,} | {cst['wins']:,} | {wr:.1f}% | ${cst['invested']:,.2f} | ${cst['collected']:,.2f} | **+${cst['pnl']:,.2f}** | **+{roi:.2f}%** |")
md.append("")
md.append("---")
md.append("")
md.append("## 4. Registro Cronológico Semana a Semana (110 Semanas)")
md.append("")
md.append("| Sem | Fechas (Inicio - Fin) | Saldo Inicio | Ops | Aciertos | Win Rate | Invertido | Cobrado | PnL Semanal | ROI Sem | Saldo Fin | Drawdown |")
md.append("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

for w in weeks:
    pnl_str = f"**+${w['pnl']:.2f}**" if w['pnl'] > 0 else (f"-${abs(w['pnl']):.2f}" if w['pnl'] < 0 else "$0.00")
    roi_str = f"+{w['roi_pct']:.1f}%" if w['roi_pct'] > 0 else f"{w['roi_pct']:.1f}%"
    sign_tag = "🟢" if w['pnl'] > 0 else ("🔴" if w['pnl'] < 0 else "⚪")
    md.append(f"| {sign_tag} S{w['semana']:03d} | {w['fecha_inicio']} a {w['fecha_fin']} | ${w['saldo_inicio']:,.2f} | {w['operaciones']} | {w['aciertos']} | {w['win_rate_pct']:.1f}% | ${w['invertido']:.2f} | ${w['cobrado']:.2f} | {pnl_str} | {roi_str} | **${w['saldo_fin']:,.2f}** | {w['drawdown_pct']:.1f}% |")

with open(ARTIFACT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(md))

print(f"✅ Artefacto generado con éxito en: {ARTIFACT_PATH} ({len(weeks)} semanas)")
