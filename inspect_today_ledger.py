import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\victo\nuevas_ruletas\ledger_nuevas_ruletas.csv', 'r', encoding='utf-8', errors='ignore') as f:
    header = f.readline().strip().split(',')
    lines = [l.strip().split(',') for l in f if l.startswith('2026-11-05')]

print(f"Header: {header}")
print(f"Total disparos hoy: {len(lines)}\n")
for l in lines:
    d = dict(zip(header, l))
    print(f"[{d.get('hora')}] {d.get('ruleta')} | Jugados: {d.get('candidatos')} | Bet: ${d.get('total_bet')} | Salido: {d.get('resultado')} | Cobrado: ${d.get('cobrado')} | PnL: ${d.get('pnl')} | Saldo: ${d.get('saldo')}")
