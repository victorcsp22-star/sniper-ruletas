import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

def analyze(name, path):
    print("=" * 60)
    print(f"ANÁLISIS DE: {name} ({path})")
    print("=" * 60)
    try:
        with open(path, mode='r', encoding='utf-8', errors='ignore') as f:
            reader = list(csv.DictReader(f))
            today_rows = [r for r in reader if '2026-11-05' in str(r.get('fecha', ''))]
            print(f"Total registros históricos: {len(reader)}")
            print(f"Total disparos HOY (2026-11-05): {len(today_rows)}")
            print("-" * 60)
            total_invested = 0.0
            total_won = 0.0
            total_pnl = 0.0
            wins = 0
            losses = 0
            for i, r in enumerate(today_rows, 1):
                h = r.get('hora', '')
                rul = r.get('ruleta', '')
                cands = r.get('candidatos', '')
                bet = float(r.get('total_bet', 0) or 0)
                res = r.get('resultado', '')
                cond = r.get('condicion', '')
                cobrado = float(r.get('cobrado', 0) or 0)
                pnl = float(r.get('pnl', 0) or 0)
                saldo = r.get('saldo', '')
                total_invested += bet
                total_won += cobrado
                total_pnl += pnl
                if 'GANADA' in cond.upper() or 'WIN' in cond.upper() or cobrado > 0:
                    wins += 1
                else:
                    losses += 1
                print(f"Disparo #{i}: [{h}] {rul}")
                print(f"   Candidatos: {cands}")
                print(f"   Apostado: ${bet:.2f} | Salido: {res} | Condición: {cond}")
                print(f"   Cobrado: ${cobrado:.2f} | PnL: ${pnl:.2f} | Saldo: ${saldo}")
                print("-" * 40)
            
            print(f"RESUMEN HOY {name}:")
            print(f"Disparos: {len(today_rows)} (Aciertos: {wins}, Fallos: {losses})")
            print(f"Inversión total: ${total_invested:.2f}")
            print(f"Cobrado total: ${total_won:.2f}")
            print(f"PnL neto hoy: ${total_pnl:+.2f}")
            if today_rows:
                print(f"Saldo final: ${today_rows[-1].get('saldo', 'N/A')}")
    except Exception as e:
        print(f"Error procesando {path}: {e}")

analyze("BOT B (Nuevas Ruletas - Dinámico)", "C:/Users/victo/nuevas_ruletas/ledger_nuevas_ruletas.csv")
analyze("BOT A (Referencia Baseline)", "C:/Users/victo/nuevas_ruletas/ledger_referencia_baseline.csv")
