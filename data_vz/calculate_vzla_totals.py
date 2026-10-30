import sys
import pandas as pd

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

df = pd.read_csv("production_ledger_venezuela.csv")

total_disparos = len(df)
ganadas = int((df["acierto"] == 1).sum())
perdidas = int((df["acierto"] == 0).sum())
win_rate = (ganadas / total_disparos * 100.0) if total_disparos > 0 else 0.0

total_invertido = df["costo_total"].sum()
total_cobrado = df["payout_cobrado"].sum()
pnl_neto = total_cobrado - total_invertido
roi = (pnl_neto / 1000.0) * 100.0

total_animales = int(df["cant_cands"].sum())
avg_unit_bet = df["apuesta_unitaria"].mean()
min_unit_bet = df["apuesta_unitaria"].min()
max_unit_bet = df["apuesta_unitaria"].max()

print("=" * 70)
print(" TOTALES AUDITADOS - BOT VENEZUELA (14-SEP A 15-OCT-2026)")
print("=" * 70)
print(f"Total Disparos Ejecutados: {total_disparos}")
print(f"Ganadas:                   {ganadas} ({win_rate:.2f}% Win Rate)")
print(f"Perdidas:                  {perdidas} ({100 - win_rate:.2f}%)")
print(f"Total Animales Apostados:  {total_animales} (promedio {total_animales/total_disparos:.2f} por sorteo)")
print(f"Inversión por Animal:      Promedio ${avg_unit_bet:.2f} USD (Rango: ${min_unit_bet:.2f} - ${max_unit_bet:.2f} USD)")
print(f"Total Invertido (Stakes):  ${total_invertido:,.2f} USD")
print(f"Total Pagado/Cobrado:      ${total_cobrado:,.2f} USD")
print(f"Beneficio Neto (PnL):      +${pnl_neto:,.2f} USD")
print(f"Rentabilidad Neta (ROI):   +{roi:.2f}% (Capital Inicial: $1,000 USD -> Balance Actual: ${1000 + pnl_neto:,.2f} USD)")
print("=" * 70)

print("\n=== DESGLOSE DETALLADO POR RULETA ===")
rows = []
for r_name, grp in df.groupby("ruleta"):
    bets = len(grp)
    w = int((grp["acierto"] == 1).sum())
    l = bets - w
    wr = (w / bets * 100.0) if bets > 0 else 0.0
    cands = int(grp["cant_cands"].sum())
    inv = grp["costo_total"].sum()
    cob = grp["payout_cobrado"].sum()
    pnl = cob - inv
    u_avg = grp["apuesta_unitaria"].mean()
    u_min = grp["apuesta_unitaria"].min()
    u_max = grp["apuesta_unitaria"].max()
    rows.append({
        "Ruleta": r_name,
        "Disparos": bets,
        "Ganadas": w,
        "Perdidas": l,
        "Win Rate": f"{wr:.1f}%",
        "Animales Jugados": cands,
        "Inv. Promedio/Animal": f"${u_avg:.2f}",
        "Rango Inv/Animal": f"${u_min:.2f} - ${u_max:.2f}",
        "Total Invertido": f"${inv:,.2f}",
        "Total Cobrado": f"${cob:,.2f}",
        "PnL Neto": f"{'+' if pnl>=0 else ''}${pnl:,.2f}"
    })

df_summary = pd.DataFrame(rows)
print(df_summary.to_string(index=False))

print("\n=== DETALLE DE LOS 14 ACIERTOS (PAGOS AL BOT) ===")
hits = df[df["acierto"] == 1]
for _, h in hits.iterrows():
    print(f"- {h['fecha']} {h['hora']} | {h['ruleta']} | Sel: {h['animales_seleccionados']} | Ganó: {h['resultado_sorteo']} | Inv: ${h['costo_total']:.2f} | Cobró: ${h['payout_cobrado']:.2f} (30x-80x) | PnL: +${h['pnl']:.2f}")
