import sys
sys.path.append(r'C:\Users\victo\nuevas_ruletas\app_movil')
import pandas as pd
import analisis_ops_diarias_top7 as aop

df = aop.get_ruletas_stats(8)
tot_dias_global = df['fecha'].nunique()

ruleta_summary = []
for r, grp in df.groupby('ruleta'):
    ops = len(grp)
    hits = len(grp[grp['hit'] == True])
    wr = hits / ops * 100
    inv = grp['cost'].sum()
    pnl = grp['pnl'].sum()
    roi = pnl / inv * 100
    ops_por_dia = ops / tot_dias_global
    
    ruleta_summary.append({
        'ruleta': r,
        'ops': ops,
        'hits': hits,
        'wr': wr,
        'inv': inv,
        'pnl': pnl,
        'roi': roi,
        'ops_dia': ops_por_dia
    })
df_r = pd.DataFrame(ruleta_summary)

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

print("="*95)
print("ANALISIS ALTERNATIVO: TOP 7 RULETAS FILTRADAS POR MAYOR EFICIENCIA (ROI %)")
print("="*95)
for idx, row in df_r_roi.iterrows():
    print(f"#{idx+1:<2} | {row['ruleta']:<28} | ROI: {row['roi']:>+6.2f}% | PnL: +${row['pnl']:>8,.1f} | Ops/Dia: {row['ops_dia']:.2f}")
print("-"*95)
print(f"Top 7 por ROI excluye a las menos eficientes: '{peores2_roi_names[0]}' y '{peores2_roi_names[1]}'")
print(f"Operaciones Diarias Promedio: {ops_dia:.2f} disparos/dia")
print(f"PnL Acumulado: +${pnl:,.1f} USD (Bs {pnl*100:,.2f})")
print(f"ROI Global del Portafolio: +{roi:.2f}% (frente a +23.73% con las 9)")
print(f"Drawdown Maximo: -${abs(max_dd):,.0f} USD (se reduce de -$484 a -${abs(max_dd):,.0f} USD)")
print(f"Dias con cobro: {dias_hit}/{tot_dias_global} ({dias_hit/tot_dias_global*100:.1f}%)")
print("="*95)
