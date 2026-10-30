import sys
import pandas as pd

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

df = pd.read_csv("lotto_activo_2anios.csv", dtype={"numero": str})
df["numero"] = df["numero"].astype(str).str.strip()
df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
df = df.sort_values(by="sort_dt").reset_index(drop=True)

lags = [20, 18, 14]
payout = 30.0

nums = df["numero"].tolist()
total_draws = len(nums)

# Simulación completa 2 años
# Rastrear:
# 1. Total sorteos
# 2. Total sorteos donde la estrategia generó candidatos (Oportunidades Teóricas/Virtuales)
# 3. Disparos Sniper Post-Fallo 1 (En cuántas invirtió)
# 4. Inversión fija $1 por animal

streak = 0
records_all = []

for i in range(max(lags) + 6, total_draws):
    fecha = df.iloc[i]["fecha"]
    hora = df.iloc[i]["hora"]
    num = nums[i]
    animal = df.iloc[i]["animal"]
    
    rec6 = set(nums[i-6:i])
    cands = list({nums[i-l] for l in lags} - rec6)
    
    if cands:
        cost = len(cands)
        hit = (num in cands)
        is_sniper_bet = (streak == 1)
        
        records_all.append({
            "fecha": fecha,
            "hora": hora,
            "numero": num,
            "animal": animal,
            "cands": cands,
            "cost": cost,
            "hit": hit,
            "streak_previa": streak,
            "participo_sniper": is_sniper_bet
        })
        
        if hit:
            streak = 0
        else:
            streak += 1

df_rec = pd.DataFrame(records_all)

def summarize_scope(df_sub, title):
    tot_draws = len(df_sub)
    opps_virtuales = len(df_sub) # Todas tuvieron cands
    cands_totales = df_sub["cost"].sum()
    hits_virtuales = df_sub["hit"].sum()
    
    # Sniper
    df_sniper = df_sub[df_sub["participo_sniper"] == True]
    disparos = len(df_sniper)
    ganadas = int(df_sniper["hit"].sum())
    perdidas = disparos - ganadas
    wr = (ganadas / disparos * 100.0) if disparos > 0 else 0.0
    
    # A $1 por animal
    fichas_apostadas = int(df_sniper["cost"].sum()) # Cada animal $1 -> total $ = sum(cost)
    total_invertido = fichas_apostadas * 1.0 # $1 por animal
    total_cobrado = ganadas * (1.0 * payout) # $30 por cada acierto
    pnl_neto = total_cobrado - total_invertido
    roi_neto = (pnl_neto / total_invertido * 100.0) if total_invertido > 0 else 0.0
    
    print("=" * 80)
    print(f" 🦁 LOTTO ACTIVO: {title}")
    print("=" * 80)
    print(f"1. Oportunidades Totales Teóricas/Virtuales: {opps_virtuales} sorteos")
    print(f"   - En estos {opps_virtuales} sorteos el sistema detectó candidatos válidos.")
    print(f"   - Aciertos globales del patrón sin filtro de racha: {hits_virtuales} ({(hits_virtuales/opps_virtuales*100):.2f}% base)")
    print()
    print(f"2. Participación Real con Gatillo Sniper Post-Fallo 1 (Racha previa = 1):")
    print(f"   - Oportunidades en las que INVIRTIÓ: {disparos} sorteos ({disparos/opps_virtuales*100:.1f}% de selectividad)")
    print(f"   - En las restantes {opps_virtuales - disparos} oportunidades NO invirtió (disciplina/espera).")
    print()
    print(f"3. Resultados Financieros Suponiendo Monto Fijo de $1 por Animal:")
    print(f"   - 🟢 Sorteos Ganados:       {ganadas} ({wr:.2f}% Win Rate)")
    print(f"   - 🔴 Sorteos Perdidos:      {perdidas} ({100 - wr:.2f}%)")
    print(f"   - Total Animales Apostados: {fichas_apostadas} animales (promedio {fichas_apostadas/disparos:.2f} por sorteo)")
    print(f"   - Inversión por sorteo:     ${fichas_apostadas/disparos:.2f} USD promedio ($1 por cada animal)")
    print(f"   - Total Invertido:          ${total_invertido:,.2f} USD (${fichas_apostadas} apuestas de $1)")
    print(f"   - Total Pagado / Cobrado:   ${total_cobrado:,.2f} USD ({ganadas} aciertos x $30.00 USD)")
    print(f"   - Beneficio Neto (PnL):     {'+' if pnl_neto>=0 else ''}${pnl_neto:,.2f} USD")
    print(f"   - Rentabilidad Neta (ROI):  {'+' if roi_neto>=0 else ''}{roi_neto:.2f}%")
    print("=" * 80)
    print()

# 1 Mes (14-Sep-2026 a hoy 15-Oct-2026)
df_rec_1m = df_rec[df_rec["fecha"] >= "2026-09-14"]
summarize_scope(df_rec_1m, "AUDITORÍA ÚLTIMO MES (14-Sep-2026 al 15-Oct-2026 | 31 Días)")

# 2 Años Completos
summarize_scope(df_rec, "BACKTEST HISTÓRICO COMPLETO (2 AÑOS: 2024 - 2026 | 8,600+ Sorteos)")

print("=== DETALLE DE LAS JUGADAS DEL ÚLTIMO MES EN LOTTO ACTIVO ($1 FIJO) ===")
df_sniper_1m = df_rec_1m[df_rec_1m["participo_sniper"] == True]
for _, row in df_sniper_1m.iterrows():
    c_list = row["cands"]
    res = f"{row['numero']} ({row['animal']})"
    status = "🟢 GANADA" if row["hit"] else "🔴 PERDIDA"
    cost = row["cost"]
    payout_amt = 30.0 if row["hit"] else 0.0
    pnl = payout_amt - cost
    print(f"{row['fecha']} {row['hora']:<8} | Cands: {str(c_list):<16} ({cost} cands = ${cost:.2f}) | Ganó: {res:<16} | {status} | Cobro: ${payout_amt:5.2f} | PnL: {pnl:+5.2f}")
