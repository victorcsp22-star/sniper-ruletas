import csv
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = r"C:\Users\victo\nuevas_ruletas"
ARTIFACT_PATH = r"C:\Users\victo\.gemini\antigravity\brain\d8f43462-caa6-4209-8905-313e89d6db4d\listado_operaciones_dias_operacion.md"

def load_rows(path):
    rows = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(r)
    return rows

base_rows = load_rows(os.path.join(ROOT_DIR, "ledger_nuevas_ruletas.csv.base_backup"))
max_rows = load_rows(os.path.join(ROOT_DIR, "ledger_nuevas_ruletas.csv"))

lines = []
lines.append("# 📜 Listado Oficial de Operaciones Día a Día (17 al 30 de Octubre de 2026)\n\n")
lines.append("> **Ubicación del Sistema:** `C:\\Users\\victo\\nuevas_ruletas\\`  \n")
lines.append("> **Capital Base Inicial:** `$200.00 USD` (17 de Octubre de 2026, 09:47 AM)  \n")
lines.append("> **Loterías Operadas:** 7 Ruletas Oficiales Multi-Activo  \n")
lines.append("> **Estado en Vivo Actual (30-Oct 12:15 PM):** **`$267.03 USD`** (**+$67.03 USD / +33.52%**) tras el acierto de las 12:00 PM en Mega Animal 40 (`#23 CEBRA`).  \n\n")
lines.append("---\n\n")

# SECTION 1: Operaciones Reales en Vivo del Sistema Actualizado (Maximizada + Multi-Agent Audit)
lines.append("## 1. Registro Completo de Operaciones del Sistema Actualizado (Estrategia Maximizada)\n\n")
lines.append(f"Listado exhaustivo de las **{len(max_rows)} operaciones** registradas día por día desde el 17 de Octubre hasta hoy 30 de Octubre a las 12:00 PM:\n\n")

from collections import defaultdict
days_max = defaultdict(list)
for r in max_rows:
    days_max[r.get("fecha", "").strip()].append(r)

m_counter = 0
for d in sorted(days_max.keys()):
    day_ops = days_max[d]
    d_wins = sum(1 for r in day_ops if "GANADA" in r.get("condicion", ""))
    d_losses = len(day_ops) - d_wins
    d_inv = sum(float(r.get("total_bet", 0) or 0) for r in day_ops)
    d_cob = sum(float(r.get("cobrado", 0) or 0) for r in day_ops)
    d_pnl = sum(float(r.get("pnl", 0) or 0) for r in day_ops)
    end_saldo = day_ops[-1].get("saldo", "---")

    pnl_sign = "+" if d_pnl >= 0 else "-"
    lines.append(f"### 📅 {d} — {len(day_ops)} Operaciones ({d_wins} Ganadas, {d_losses} Perdidas) | Invertido: `${d_inv:.2f}` | PnL Día: `{pnl_sign}${abs(d_pnl):.2f}` | Saldo: `${end_saldo}`\n\n")
    lines.append("| N° | Hora | Ruleta | Animales Jugados | Salido Oficial | Resultado | Inversión ($) | Cobrado ($) | PnL ($) | Saldo ($) |\n")
    lines.append("| :---: | :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")

    for r in day_ops:
        m_counter += 1
        h = r.get("hora", "")
        rul = r.get("ruleta", "")
        cands = r.get("candidatos", "")
        res = r.get("resultado", "")
        cond = "🟢 GANADA" if "GANADA" in r.get("condicion", "") else "🔴 PERDIDA"
        inv = float(r.get("total_bet", 0) or 0)
        cob = float(r.get("cobrado", 0) or 0)
        pnl = float(r.get("pnl", 0) or 0)
        saldo = float(r.get("saldo", 0) or 0)
        pnl_str = f"{'+' if pnl>=0 else ''}${pnl:.2f}"
        lines.append(f"| {m_counter} | {h} | {rul} | `{cands}` | **{res}** | {cond} | ${inv:.2f} | ${cob:.2f} | **{pnl_str}** | **${saldo:.2f}** |\n")
    lines.append("\n")

lines.append("---\n\n")

# SECTION 2: Resumen Diario Comparativo
lines.append("## 2. Resumen Estadístico Consolidado por Día\n\n")
lines.append("| Fecha | Operaciones | Ganadas | Perdidas | Win Rate (%) | Total Invertido | Total Cobrado | PnL del Día | Saldo Cierre |\n")
lines.append("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n")

for d in sorted(days_max.keys()):
    day_ops = days_max[d]
    d_wins = sum(1 for r in day_ops if "GANADA" in r.get("condicion", ""))
    d_losses = len(day_ops) - d_wins
    wr = (d_wins / len(day_ops) * 100.0) if day_ops else 0.0
    d_inv = sum(float(r.get("total_bet", 0) or 0) for r in day_ops)
    d_cob = sum(float(r.get("cobrado", 0) or 0) for r in day_ops)
    d_pnl = sum(float(r.get("pnl", 0) or 0) for r in day_ops)
    end_saldo = float(day_ops[-1].get("saldo", 0) or 0)
    pnl_str = f"{'+' if d_pnl>=0 else ''}${d_pnl:.2f}"
    lines.append(f"| **{d}** | {len(day_ops)} | {d_wins} | {d_losses} | {wr:.1f}% | ${d_inv:.2f} | ${d_cob:.2f} | **{pnl_str}** | **${end_saldo:.2f}** |\n")

lines.append("\n---\n\n")

# SECTION 3: Registro Previo de la Estrategia Base (Antes de la Actualización)
lines.append("## 3. Registro Histórico de la Estrategia Base (Antes de la Actualización)\n\n")
lines.append(f"Historial de las **{len(base_rows)} operaciones** registradas por la versión base (saldo pico alcanzado de `$305.16 USD` el 27 de Octubre):\n\n")

days_base = defaultdict(list)
for r in base_rows:
    days_base[r.get("fecha", "").strip()].append(r)

b_counter = 0
for d in sorted(days_base.keys()):
    day_ops = days_base[d]
    d_wins = sum(1 for r in day_ops if "GANADA" in r.get("condicion", ""))
    d_inv = sum(float(r.get("total_bet", 0) or 0) for r in day_ops)
    d_pnl = sum(float(r.get("pnl", 0) or 0) for r in day_ops)
    end_saldo = day_ops[-1].get("saldo", "---")
    pnl_sign = "+" if d_pnl >= 0 else "-"

    lines.append(f"#### 📅 {d} — {len(day_ops)} Ops | {d_wins} Ganadas | PnL: `{pnl_sign}${abs(d_pnl):.2f}` | Saldo: `${end_saldo}`\n\n")
    lines.append("| N° | Hora | Ruleta | Animales Jugados | Salido Oficial | Condición | Invertido ($) | Cobrado ($) | PnL ($) | Saldo ($) |\n")
    lines.append("| :---: | :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")

    for r in day_ops:
        b_counter += 1
        h = r.get("hora", "")
        rul = r.get("ruleta", "")
        cands = r.get("candidatos", "")
        res = r.get("resultado", "")
        cond = "🟢 GANADA" if "GANADA" in r.get("condicion", "") else "🔴 PERDIDA"
        inv = float(r.get("total_bet", 0) or 0)
        cob = float(r.get("cobrado", 0) or 0)
        pnl = float(r.get("pnl", 0) or 0)
        saldo = float(r.get("saldo", 0) or 0)
        pnl_str = f"{'+' if pnl>=0 else ''}${pnl:.2f}"
        lines.append(f"| {b_counter} | {h} | {rul} | `{cands}` | **{res}** | {cond} | ${inv:.2f} | ${cob:.2f} | **{pnl_str}** | **${saldo:.2f}** |\n")
    lines.append("\n")

with open(ARTIFACT_PATH, "w", encoding="utf-8") as f:
    f.writelines(lines)

print(f"Artifact created at {ARTIFACT_PATH}")
