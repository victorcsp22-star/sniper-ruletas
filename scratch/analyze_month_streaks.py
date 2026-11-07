import pandas as pd

df = pd.read_csv(r'C:\Users\victo\nuevas_ruletas\ledger_nuevas_ruletas.csv')
df['fecha'] = pd.to_datetime(df['fecha'])
m_df = df[(df['fecha'] >= '2026-09-30') & (df['fecha'] <= '2026-10-30')].copy()

# Semanas exactas de 7 días
w1 = m_df[(m_df['fecha'] >= '2026-09-30') & (m_df['fecha'] <= '2026-10-06')]
w2 = m_df[(m_df['fecha'] >= '2026-10-07') & (m_df['fecha'] <= '2026-10-13')]
w3 = m_df[(m_df['fecha'] >= '2026-10-14') & (m_df['fecha'] <= '2026-10-20')]
w4 = m_df[(m_df['fecha'] >= '2026-10-21') & (m_df['fecha'] <= '2026-10-27')]
w5 = m_df[(m_df['fecha'] >= '2026-10-28') & (m_df['fecha'] <= '2026-10-30')]

weeks = [
    ("Semana 1 (30 Sep - 06 Oct)", w1),
    ("Semana 2 (07 Oct - 13 Oct)", w2),
    ("Semana 3 (14 Oct - 20 Oct)", w3),
    ("Semana 4 (21 Oct - 27 Oct)", w4),
    ("Semana 5 (28 Oct - 30 Oct)", w5)
]

print("="*60)
print("REPORTE SEMANAL DE GANANCIAS (CICLOS DE RETIRO)")
print("="*60)
tot_pnl = 0
for name, w in weeks:
    pnl = w['pnl'].sum()
    bet = w['total_bet'].sum()
    cob = w['cobrado'].sum()
    wins = (w['cobrado'] > 0).sum()
    ops = len(w)
    wr = (wins / ops * 100) if ops > 0 else 0
    tot_pnl += pnl
    print(f"{name}:")
    print(f"  Operaciones: {ops} | Aciertos: {wins} ({wr:.1f}%)")
    print(f"  Inversión: ${bet:.2f} | Cobrado: ${cob:.2f} | PnL: +${pnl:.2f}")

print("="*60)
print(f"PNL NETO TOTAL DEL MES: +${tot_pnl:.2f} USD")
print("="*60)
