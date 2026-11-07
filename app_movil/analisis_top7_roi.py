import sys
sys.path.append(r'C:\Users\victo\nuevas_ruletas\app_movil')
import pandas as pd
from analisis_ops_diarias_top7 import df, df_r, tot_dias_global

# Ordenar por ROI %
df_r_roi = df_r.sort_values(by='roi', ascending=False).reset_index(drop=True)
top7_roi_names = df_r_roi.head(7)['ruleta'].tolist()
peores2_roi_names = df_r_roi.tail(2)['ruleta'].tolist()

df_top7_roi = df[df['ruleta'].isin(top7_roi_names)].copy().reset_index(drop=True)

tot_ops = len(df_top7_roi)
ops_dia = tot_ops / tot_dias_global
inv = df_top7_roi['cost'].sum()
pnl = df_top7_roi['pnl'].sum()
roi = pnl / inv * 100
wr = len(df_top7_roi[df_top7_roi['hit']==True]) / tot_ops * 100

# DD
df_top7_roi['cum_pnl'] = df_top7_roi['pnl'].cumsum()
df_top7_roi['peak'] = df_top7_roi['cum_pnl'].cummax()
max_dd = (df_top7_roi['cum_pnl'] - df_top7_roi['peak']).min()

# Dias cobro
dias_hit = len([grp for _, grp in df_top7_roi.groupby('fecha') if len(grp[grp['hit']==True]) >= 1])

print("="*90)
print("RANKING POR ROI % (RENTABILIDAD POR DOLAR INVERTIDO):")
print("="*90)
for idx, row in df_r_roi.iterrows():
    print(f"#{idx+1:<2} | {row['ruleta']:<28} | ROI: {row['roi']:>+6.2f}% | PnL: +${row['pnl']:>9,.1f} | Ops/Dia: {row['ops_dia']:.2f}")
print("-"*90)
print(f"Top 7 por ROI excluye a: {peores2_roi_names[0]} y {peores2_roi_names[1]}")
print(f"Ops/dia promedio Top 7 ROI: {ops_dia:.2f} tiros/dia")
print(f"PnL Top 7 ROI: +${pnl:,.1f} USD | ROI: +{roi:.2f}% | Max DD: -${abs(max_dd):,.0f} USD")
print(f"Dias con cobro: {dias_hit}/{tot_dias_global} ({dias_hit/tot_dias_global*100:.1f}%)")
print("="*90)
