import sys
from streak_entry_matrix import evaluate_streak_entries, CONFIG

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

for name in ['Gatazo', 'Mega Animal 40', 'Lotto Gato']:
    res = evaluate_streak_entries(name, CONFIG[name])
    print("=" * 110)
    print(f" {res['emoji']} {name.upper()} | Payout: {res['payout']:.0f}x | Break-Even: {res['be_rate']:.2f}% | Lags: {res['lags']}")
    print("=" * 110)
    print(f" {'Punto de Entrada':<34} | {'Sorteos':<8} | {'Animales':<9} | {'Ganadas':<8} | {'Perdidas':<9} | {'Win Rate':<10} | {'Total Inv. ($)':<14} | {'Cobrado ($)':<12} | {'PnL Neto ($)':<14} | {'ROI Neto'}")
    print("-" * 125)
    for _, row in res['df_streaks'].iterrows():
        pnl_str = f"{'+' if row['pnl']>=0 else ''}${row['pnl']:,.2f}"
        roi_str = f"{row['roi']:+.1f}%" if row['disparos'] > 0 else "N/A"
        wr_str = f"{row['win_rate']:.2f}%" if row['disparos'] > 0 else "0.00%"
        inv_str = f"${row['invested']:,.2f}"
        cob_str = f"${row['collected']:,.2f}"
        badge = "🟢" if row['pnl'] > 0 else ("🔴" if row['disparos'] > 0 else "⚪")
        print(f" {badge} {row['label']:<32} | {row['disparos']:>7} | {row['fichas']:>8} | {row['ganadas']:>7} | {row['perdidas']:>8} | {wr_str:>9} | {inv_str:>13} | {cob_str:>11} | {pnl_str:>13} | {roi_str:>8}")
    print()
