import pandas as pd
import numpy as np

ledger = pd.read_csv(r"C:\Users\victo\nuevas_ruletas\ledger_nuevas_ruletas.csv")
print(f"Total live rows: {len(ledger)}")
print(ledger.columns.tolist())
print(f"Dates: {ledger['fecha'].min()} to {ledger['fecha'].max()}")
hits = ledger[ledger['condicion'].str.contains('GANADA', na=False)]
losses = ledger[ledger['condicion'].str.contains('PERDIDA', na=False)]
print(f"Wins: {len(hits)}, Losses: {len(losses)}, Total: {len(hits)+len(losses)}")
print(f"Live Win Rate: {len(hits)/len(ledger)*100:.2f}%")
inv = ledger['total_bet'].sum()
cob = ledger['cobrado'].sum()
pnl = ledger['pnl'].sum()
print(f"Total Invested: ${inv:.2f}, Total Won: ${cob:.2f}, Net PnL: ${pnl:.2f}")
print(f"ROI: {pnl/inv*100:.2f}%")
print(f"Starting balance: ${ledger['saldo'].iloc[0] - ledger['pnl'].iloc[0]:.2f}")
print(f"Final balance: ${ledger['saldo'].iloc[-1]:.2f}")
print(f"Max Drawdown live: {ledger['drawdown_pct'].max()}%")
